"""Direct repair orchestration and records, without loading evaluator inputs."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from uuid import uuid4

from vericode import __version__
from vericode.datasets import TaskManifest
from vericode.docker_executor import DockerExecutor
from vericode.experiments import _git_revision
from vericode.jobs import CandidateExecutor, MockJobExecutor
from vericode.model_io import PROMPT_VERSION, RepairRequest, summarize_calls
from vericode.providers import MockProvider
from vericode.run_config import RunConfiguration
from vericode.schemas import RepairTask, ValidationError
from vericode.strategies import direct_repair


def make_executor(config: RunConfiguration) -> CandidateExecutor:
    return DockerExecutor(config.image, config.execution) if config.backend == "docker" else MockJobExecutor()


def record_direct_task(task: RepairTask, config: RunConfiguration, executor: CandidateExecutor | None = None) -> dict:
    provider = MockProvider(config.model, config.generation)
    outcome = direct_repair(task, provider, executor if executor is not None else make_executor(config))
    calls = outcome.calls
    attempts = int(bool(calls))
    responses = sum(call.status in ("completed", "invalid_response") for call in calls)
    return {
        "schema_version": 1, "run_id": str(uuid4()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_kind": "mock" if config.backend == "mock" else "sandbox_smoke",
        "strategy": "direct", "package_version": __version__,
        "git_commit": _git_revision(), "task_id": task.task_id,
        "dataset_version": task.dataset_version, "split": task.split,
        "configuration": config.to_dict(), "paid_api_enabled": False,
        "prompt_version": PROMPT_VERSION, "prompt": RepairRequest(task).prompt(),
        "source_sha256": hashlib.sha256(task.source.encode("utf-8")).hexdigest(),
        "visible_tests_sha256": hashlib.sha256(task.repair_tests.encode("utf-8")).hexdigest(),
        "status": outcome.status, "detail": outcome.detail,
        "candidate": asdict(outcome.candidate) if outcome.candidate else None,
        "candidate_changed": outcome.candidate.replacement_source != task.source if outcome.candidate else None,
        "patch": outcome.patch, "repair_execution": asdict(outcome.execution) if outcome.execution else None,
        "evaluation": None, "agent_accepted": outcome.agent_accepted,
        "usage": {"attempts": attempts, "repair_responses": responses, **summarize_calls(calls)},
        "model_calls": [asdict(call) for call in calls],
        "controller_duration_seconds": outcome.duration_seconds,
        "attempt_history": [{"attempt": 1, "status": outcome.status,
                             "candidate": asdict(outcome.candidate) if outcome.candidate else None}] if attempts else [],
        "limitations": [
            "Scripted mock provider; no live model or final evaluation was used.",
            "Post-response visible checks never feed back into direct repair.",
            "Visible-test success is not proof of correctness.",
            "Unknown failed-call usage remains unknown; known subtotals exclude it.",
            "Git commit identifies HEAD; local uncommitted edits may affect this run.",
        ],
    }


def run_direct(data_root: Path, task_id: str, config: RunConfiguration) -> dict:
    manifest = TaskManifest.load(data_root / "manifests/development.json")
    tasks = {task.task_id: task for task in manifest.load_tasks(data_root / "repair")}
    if manifest.split != "development" or task_id not in tasks:
        raise ValidationError(f"{task_id!r}: not listed in the development manifest")
    return record_direct_task(tasks[task_id], config)
