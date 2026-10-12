"""Validate and stage a full-file replacement without executing its contents."""

import ast
from contextlib import contextmanager
import difflib
from pathlib import Path
from tempfile import TemporaryDirectory
from collections.abc import Iterator

from vericode.schemas import Candidate, RepairTask, ValidationError


def validate_candidate(task: RepairTask, candidate: Candidate) -> None:
    if candidate.task_id != task.task_id:
        raise ValidationError("candidate task_id does not match the repair task")
    if candidate.target_file != task.task_file or candidate.target_file != "solution.py":
        raise ValidationError("candidate target must be the permitted task file")
    try:
        tree = ast.parse(candidate.replacement_source, filename="solution.py")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise ValidationError(f"candidate is not parseable Python: {exc}") from exc
    if not any(isinstance(node, ast.FunctionDef) and node.name == task.entry_point for node in tree.body):
        raise ValidationError(f"candidate must define top-level function {task.entry_point!r}")
    # Parsing verifies shape only. Arbitrary imports and top-level side effects
    # remain untrusted and must never run on the host.


def preview_diff(task: RepairTask, candidate: Candidate) -> str:
    validate_candidate(task, candidate)
    lines = difflib.unified_diff(
        task.source.splitlines(), candidate.replacement_source.splitlines(),
        fromfile="a/solution.py", tofile="b/solution.py", lineterm="",
    )
    preview = "\n".join(lines)
    return preview + "\n" if preview else ""


@contextmanager
def candidate_workspace(task: RepairTask, candidate: Candidate) -> Iterator[Path]:
    """Create a fresh host-side staging directory; this is NOT an execution sandbox."""
    validate_candidate(task, candidate)
    with TemporaryDirectory(prefix="vericode-") as directory:
        workspace = Path(directory)
        (workspace / "solution.py").write_text(candidate.replacement_source, encoding="utf-8")
        (workspace / "test_visible.py").write_text(task.repair_tests, encoding="utf-8")
        yield workspace
