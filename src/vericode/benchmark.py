"""Verify frozen repair data without opening evaluator assets."""

from dataclasses import asdict
from pathlib import Path

from vericode.checkpoints import fingerprint
from vericode.datasets import TaskManifest, read_json
from vericode.schemas import ValidationError

QUIXBUGS_REVISION = "4257f44b0ff1181dedaedee6a447e133219fcebf"
QUIXBUGS_VERSION = "quixbugs-4257f44-v1"


def verify_repair_freeze(data_root: Path) -> dict:
    freeze = read_json(data_root / "manifests/repair_freeze.json")
    seen = set()
    for split in ("development", "final"):
        path = data_root / f"manifests/{split}.json"
        manifest = TaskManifest.load(path)
        if manifest.split != split or seen.intersection(manifest.task_ids):
            raise ValidationError("frozen task splits overlap or mismatch")
        seen.update(manifest.task_ids)
        tasks = manifest.load_tasks(data_root / "repair")
        actual = {"manifest": fingerprint(read_json(path)),
                  "tasks": {task.task_id: fingerprint(asdict(task)) for task in tasks}}
        if actual != freeze["splits"][split]:
            raise ValidationError(f"{split}: repair manifest/task freeze mismatch")
    return freeze
