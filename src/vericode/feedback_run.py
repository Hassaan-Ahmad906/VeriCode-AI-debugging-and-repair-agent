"""Feedback repair records and CLI orchestration without evaluator loading."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from uuid import uuid4

from vericode import __version__
from vericode.datasets import TaskManifest
from vericode.direct_run import make_executor
from vericode.experiments import _git_revision
from vericode.feedback import FEEDBACK_PROMPT_VERSION, feedback_repair
from vericode.jobs import CandidateExecutor
from vericode.model_io import summarize_calls
from vericode.providers import MockProvider
from vericode.run_config import FeedbackConfiguration
from vericode.schemas import RepairTask, ValidationError


def record_feedback_task(task: RepairTask, config: FeedbackConfiguration,
                         executor: CandidateExecutor | None = None) -> dict:
    outcome = feedback_repair(task, MockProvider(config.model, config.generation),
                              executor if executor is not None else make_executor(config), config.feedback)
    return {
        "schema_version": 2, "run_id": str(uuid4()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_kind": "mock" if config.backend == "mock" else "sandbox_smoke",
        "strategy": config.strategy, "package_version": __version__,
        "git_commit": _git_revision(), "task_id": task.task_id,
        "dataset_version": task.dataset_version, "split": task.split,
        "configuration": config.to_dict(), "paid_api_enabled": False,
        "prompt_version": FEEDBACK_PROMPT_VERSION,
        "source_sha256": hashlib.sha256(task.source.encode("utf-8")).hexdigest(),
        "visible_tests_sha256": hashlib.sha256(task.repair_tests.encode("utf-8")).hexdigest(),
        "status": outcome.status, "detail": outcome.detail,
        "candidate": asdict(outcome.candidate) if outcome.candidate else None,
        "candidate_changed": outcome.candidate.replacement_source != task.source if outcome.candidate else None,
        "patch": outcome.patch,
        "initial_execution": asdict(outcome.initial_execution) if outcome.initial_execution else None,
        "repair_execution": asdict(outcome.execution) if outcome.execution else None,
        "evaluation": None, "agent_accepted": outcome.agent_accepted,
        "usage": {"repair_requests": len(outcome.history),
                  "attempts": sum(bool(attempt.call_indices) for attempt in outcome.history),
                  "repair_responses": sum(call.status in ("completed", "invalid_response") for call in outcome.calls),
                  **summarize_calls(outcome.calls)},
        "model_calls": [asdict(call) for call in outcome.calls],
        "attempt_history": [asdict(attempt) for attempt in outcome.history],
        "controller_duration_seconds": outcome.duration_seconds,
        "limitations": [
            "Scripted mock provider; no live-model or final-evaluation result.",
            "Visible-test success, including original-source success, is not proof of correctness.",
            "Test output is untrusted data; feedback projection is not a prompt-injection guarantee.",
            "Unknown failed-call usage remains unknown; known subtotals exclude it.",
            "History retains rejected proposals; final candidate is the latest validated proposal submitted for checking.",
            "Git commit identifies HEAD; local uncommitted edits may affect this run.",
        ],
    }


def run_feedback(data_root: Path, task_id: str, config: FeedbackConfiguration) -> dict:
    manifest = TaskManifest.load(data_root / "manifests/development.json")
    tasks = {task.task_id: task for task in manifest.load_tasks(data_root / "repair")}
    if manifest.split != "development" or task_id not in tasks:
        raise ValidationError(f"{task_id!r}: not listed in the development manifest")
    return record_feedback_task(tasks[task_id], config)
