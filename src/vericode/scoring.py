"""Post-repair evaluator. No model/provider calls and no feedback into repair."""

from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from time import monotonic
from uuid import uuid4

from vericode.checkpoints import fingerprint
from vericode.datasets import TaskManifest, read_json
from vericode.direct_run import make_executor
from vericode.evaluation import load_evaluation_suite
from vericode.patches import validate_candidate
from vericode.results import ExecutionResult
from vericode.run_config import RunConfiguration
from vericode.schemas import Candidate, ValidationError


def _execute(executor, source, tests):
    try:
        result = executor.run(source, tests)
        if not isinstance(result, ExecutionResult):
            raise TypeError("invalid execution contract")
    except Exception:
        return ExecutionResult("sandbox", "infrastructure_error", detail="Evaluator adapter failed; private exception details omitted.")
    if result.cleanup_confirmed is False:
        return replace(result, status="infrastructure_error", tests_passed=None, tests_failed=None,
                       tests_errors=None, tests_skipped=None, detail="Evaluator cleanup is unconfirmed; further jobs blocked.")
    return result


def score_record(data_root: Path, repair: dict, config: RunConfiguration, executor=None) -> dict:
    started = monotonic()
    if not isinstance(repair, dict) or repair.get("split") not in ("development", "final"):
        raise ValidationError("repair record: missing/invalid task split")
    recorded_config = RunConfiguration.from_dict(repair.get("configuration"))
    if repair.get("schema_version") != recorded_config.to_dict()["schema_version"] or repair.get("strategy") != recorded_config.strategy:
        raise ValidationError("repair record: strategy/schema mismatch")
    if type(repair.get("agent_accepted")) not in (bool, type(None)):
        raise ValidationError("repair record: invalid acceptance decision")
    manifest = TaskManifest.load(data_root / f"manifests/{repair['split']}.json")
    tasks = {task.task_id: task for task in manifest.load_tasks(data_root / "repair")}
    task = tasks.get(repair.get("task_id"))
    if task is None or repair.get("dataset_version") != task.dataset_version:
        raise ValidationError("repair record: task/version differs from manifest")
    for field, text in (("source_sha256", task.source), ("visible_tests_sha256", task.repair_tests)):
        if repair.get(field) != hashlib.sha256(text.encode("utf-8")).hexdigest():
            raise ValidationError(f"repair record: {field} mismatch")
    candidate = Candidate.from_dict(repair["candidate"]) if repair.get("candidate") is not None else None
    rejected_candidate = False
    if candidate is not None:
        try:
            validate_candidate(task, candidate)
        except ValidationError:
            if repair.get("status") != "invalid_patch":
                raise
            candidate = None
            rejected_candidate = True
    # Evaluator files are opened only after validating the completed repair input.
    suite = load_evaluation_suite(data_root / "evaluation", task.task_id)
    if suite.dataset_version != task.dataset_version:
        raise ValidationError("evaluation/task versions differ")
    freeze = read_json(data_root / "benchmark/evaluation_freeze.json")
    if fingerprint(asdict(suite)) != freeze["splits"][task.split][task.task_id]:
        raise ValidationError("evaluation suite freeze mismatch")
    executor = executor if executor is not None else make_executor(config)
    baseline = _execute(executor, task.source, suite.tests)
    observed = None
    if candidate is not None and baseline.status != "infrastructure_error":
        observed = _execute(executor, candidate.replacement_source, suite.tests)
    baseline_passed = {"passed": True, "failed": False}.get(baseline.status)
    candidate_passed = {"passed": True, "failed": False}.get(observed.status) if observed else None
    infrastructure_error = baseline.status == "infrastructure_error" or observed is not None and observed.status == "infrastructure_error"
    regression = (baseline_passed and not candidate_passed) if baseline_passed is not None and candidate_passed is not None else None
    overfit = (repair["agent_accepted"] and not candidate_passed) if repair["agent_accepted"] is not None and candidate_passed is not None else None
    return {
        "schema_version": 1, "evaluation_id": str(uuid4()), "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_kind": "mock" if config.backend == "mock" else "sandbox_evaluation_smoke",
        "repair_run_id": repair.get("run_id"), "repair_record_sha256": fingerprint(repair),
        "task_id": task.task_id, "dataset_version": task.dataset_version, "split": task.split,
        "strategy": repair["strategy"], "status": "infrastructure_error" if infrastructure_error else "scored" if candidate else "no_candidate",
        "repair_status": repair.get("status"), "rejected_candidate": rejected_candidate,
        "configuration": config.to_dict(), "suite_sha256": fingerprint(asdict(suite)),
        "baseline_source_sha256": hashlib.sha256(task.source.encode("utf-8")).hexdigest(),
        "candidate_source_sha256": hashlib.sha256(candidate.replacement_source.encode("utf-8")).hexdigest() if candidate else None,
        "baseline_execution": asdict(baseline), "candidate_execution": asdict(observed) if observed else None,
        "baseline_suite_passed": baseline_passed, "suite_passed": candidate_passed,
        "agent_accepted": repair["agent_accepted"], "regression": regression, "accepted_but_failed": overfit,
        "model_calls": 0, "api_cost_usd": 0.0, "controller_duration_seconds": monotonic() - started,
        "limitations": ["Post-repair observations are never supplied to a repair provider.",
                        "Unknown timeouts/test errors/infrastructure are separate from observed assertion failures.",
                        "Suite success is finite-test evidence, not proof; mock repairs do not measure LLM ability."],
    }
