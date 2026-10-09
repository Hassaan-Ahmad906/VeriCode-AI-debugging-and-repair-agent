"""Offline orchestration and JSON artifacts; no performance analysis yet."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any
from uuid import uuid4

from vericode import __version__
from vericode.datasets import TaskManifest
from vericode.evaluation import evaluate_mock, load_evaluation_suite
from vericode.providers import MockProvider, PROMPT_VERSION
from vericode.repair import repair_once_mock
from vericode.schemas import ValidationError


def _git_revision() -> str | None:
    """Trusted controller metadata only; candidate code never gets a shell."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True, text=True, timeout=2, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def run_mock_demo(data_root: Path, task_id: str) -> dict[str, Any]:
    manifest = TaskManifest.load(data_root / "manifests/development.json")
    tasks = {task.task_id: task for task in manifest.load_tasks(data_root / "repair")}
    if manifest.split != "development" or task_id not in tasks:
        raise ValidationError(f"{task_id!r}: not listed in the development manifest")
    task = tasks[task_id]
    repair = repair_once_mock(task, MockProvider())
    # The final candidate is already chosen; these objects never enter repair.
    suite = load_evaluation_suite(data_root / "evaluation", task_id)
    if suite.dataset_version != task.dataset_version:
        raise ValidationError("evaluation dataset version differs from the repair task")
    evaluation = evaluate_mock(repair.response.candidate, suite)
    return {
        "schema_version": 1,
        "run_id": str(uuid4()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_kind": "mock",
        "strategy": "mock_demo",
        "package_version": __version__,
        "git_commit": _git_revision(),
        "task_id": task_id,
        "dataset_version": task.dataset_version,
        "split": task.split,
        "prompt_version": PROMPT_VERSION,
        "prompt": repair.prompt,
        "source_sha256": hashlib.sha256(task.source.encode("utf-8")).hexdigest(),
        "provider": repair.response.provider,
        "model": repair.response.model,
        "candidate": asdict(repair.response.candidate),
        "patch": repair.patch,
        "repair_execution": asdict(repair.execution),
        "evaluation": asdict(evaluation),
        "agent_accepted": None,
        "usage": {
            "attempts": repair.attempts,
            "model_calls": repair.model_calls,
            "input_tokens": repair.response.input_tokens,
            "output_tokens": repair.response.output_tokens,
            "cost_usd": repair.response.cost_usd,
        },
        "configuration": {
            "paid_api_enabled": False,
            "spending_cap_usd": 0,
            "max_attempts": 1,
            "max_model_calls": 1,
            "execution_backend": "mock",
            "execution_limits": None,
            "random_seed": None,
        },
        "limitations": [
            "Scripted mock response; no live model was called.",
            "No candidate or test code was executed; success and acceptance are unknown.",
            "Development demonstration only, not a measured repair result.",
            "Git commit identifies HEAD; local uncommitted edits may also affect a run.",
        ],
    }


def write_run(path: Path, record: dict[str, Any]) -> None:
    """Create one UTF-8 JSON artifact and refuse to overwrite existing work."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(serialized)
