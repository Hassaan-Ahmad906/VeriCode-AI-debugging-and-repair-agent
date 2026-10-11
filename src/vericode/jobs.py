"""Immutable repair-visible execution inputs and local smoke-check records."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from vericode.datasets import TaskManifest
from vericode.docker_executor import DockerExecutor
from vericode.experiments import _git_revision
from vericode.patches import validate_candidate
from vericode.providers import MockProvider, RepairRequest
from vericode.results import ExecutionResult
from vericode.sandbox_policy import DEFAULT_IMAGE, ExecutionLimits
from vericode.schemas import Candidate, RepairTask, ValidationError, require_id, require_text


class CandidateExecutor(Protocol):
    def run(self, source: str, tests: str) -> ExecutionResult: ...


@dataclass(frozen=True)
class VisibleJob:
    task_id: str
    source: str
    tests: str

    def __post_init__(self) -> None:
        require_id(self.task_id)
        require_text(self.source, "job source")
        require_text(self.tests, "job tests")

    @classmethod
    def from_task(cls, task: RepairTask, candidate: Candidate | None = None) -> "VisibleJob":
        if candidate is not None:
            validate_candidate(task, candidate)
        return cls(task.task_id, candidate.replacement_source if candidate else task.source, task.repair_tests)

    def execute(self, executor: CandidateExecutor) -> ExecutionResult:
        # Send contents, never host paths, repository roots, or evaluator objects.
        return executor.run(self.source, self.tests)


class MockJobExecutor:
    def run(self, source: str, tests: str) -> ExecutionResult:
        require_text(source, "mock source")
        require_text(tests, "mock tests")
        return ExecutionResult("mock", "not_executed", detail="MOCK: visible job validated; no code executed.")


def run_visible_check(
    data_root: Path, task_id: str, *, backend: str = "mock", candidate_origin: str = "original",
    image: str = DEFAULT_IMAGE, limits: ExecutionLimits | None = None,
) -> dict:
    if backend not in ("mock", "docker") or candidate_origin not in ("original", "mock"):
        raise ValidationError("expected mock/docker backend and original/mock candidate")
    manifest = TaskManifest.load(data_root / "manifests/development.json")
    tasks = {task.task_id: task for task in manifest.load_tasks(data_root / "repair")}
    if manifest.split != "development" or task_id not in tasks:
        raise ValidationError(f"{task_id!r}: not listed in the development manifest")
    task = tasks[task_id]
    candidate = MockProvider().propose(RepairRequest(task)).candidate if candidate_origin == "mock" else None
    job = VisibleJob.from_task(task, candidate)
    limits = limits or ExecutionLimits()
    executor = DockerExecutor(image, limits) if backend == "docker" else MockJobExecutor()
    execution = job.execute(executor)
    return {
        "schema_version": 1, "run_id": str(uuid4()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_kind": "mock" if backend == "mock" else "sandbox_smoke",
        "strategy": "visible_check", "task_id": task_id,
        "dataset_version": task.dataset_version, "split": task.split,
        "git_commit": _git_revision(), "candidate_origin": candidate_origin,
        "candidate_source": job.source,
        "source_sha256": hashlib.sha256(job.source.encode("utf-8")).hexdigest(),
        "visible_tests_sha256": hashlib.sha256(job.tests.encode("utf-8")).hexdigest(),
        "execution": asdict(execution), "evaluation": None,
        "usage": {"model_calls": 1 if candidate else 0, "input_tokens": None,
                  "output_tokens": None, "cost_usd": 0.0},
        "configuration": {"backend": backend, "paid_api_enabled": False,
                          "image": image if backend == "docker" else None,
                          "limits": asdict(limits) if backend == "docker" else None},
        "limitations": [
            "Visible-test development smoke check, not final evaluation or a live-model experiment.",
            "Passing these tests is not proof of correctness.",
            "Git commit identifies HEAD; local uncommitted edits may affect this run.",
        ],
    }
