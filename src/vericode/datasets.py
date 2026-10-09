"""Load bounded JSON data, never importing or executing fixture code."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from vericode.schemas import (
    RepairTask, ValidationError, require_fields, require_id, require_text, require_version,
)

MAX_JSON_BYTES = 65_536


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"JSON: duplicate field {key!r}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValidationError(f"JSON exceeds {MAX_JSON_BYTES} bytes")
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def contained_file(root: Path, task_id: str, filename: str) -> Path:
    require_id(task_id)
    root = root.resolve()
    path = (root / task_id / filename).resolve()
    if not path.is_relative_to(root):
        raise ValidationError("fixture path escapes its dataset root")
    return path


def load_task(repair_root: Path, task_id: str) -> RepairTask:
    task = RepairTask.from_dict(read_json(contained_file(repair_root, task_id, "task.json")))
    if task.task_id != task_id:
        raise ValidationError(f"task_id: requested {task_id!r}, loaded {task.task_id!r}")
    return task


@dataclass(frozen=True)
class TaskManifest:
    schema_version: int
    dataset_version: str
    split: str
    task_ids: tuple[str, ...]

    @classmethod
    def load(cls, path: Path) -> "TaskManifest":
        data = require_fields(read_json(path), set(cls.__dataclass_fields__), "manifest")
        require_version(data["schema_version"])
        require_text(data["dataset_version"], "dataset_version")
        if data["split"] not in ("development", "final"):
            raise ValidationError("manifest split: expected 'development' or 'final'")
        ids = data["task_ids"]
        if not isinstance(ids, list):
            raise ValidationError("task_ids: expected a list")
        for task_id in ids:
            require_id(task_id)
        if len(ids) != len(set(ids)):
            raise ValidationError("task_ids: duplicate task identifiers")
        return cls(data["schema_version"], data["dataset_version"], data["split"], tuple(ids))

    def load_tasks(self, repair_root: Path) -> tuple[RepairTask, ...]:
        tasks = tuple(load_task(repair_root, task_id) for task_id in self.task_ids)
        for task in tasks:
            if task.split != self.split or task.dataset_version != self.dataset_version:
                raise ValidationError(f"{task.task_id}: split/version differs from manifest")
        return tasks
