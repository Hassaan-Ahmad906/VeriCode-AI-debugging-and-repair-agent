"""UI actions share the CLI controllers; repair never opens evaluator assets."""

from pathlib import Path

from vericode.augmented import record_augmented_task
from vericode.datasets import TaskManifest
from vericode.direct_run import record_direct_task
from vericode.feedback_run import record_feedback_task
from vericode.run_config import RunConfiguration
from vericode.schemas import ValidationError
from vericode.scoring import score_record


def development_tasks(data_root: Path):
    manifest = TaskManifest.load(data_root / "manifests/development.json")
    if manifest.split != "development":
        raise ValidationError("UI requires the development manifest")
    return manifest.load_tasks(data_root / "repair")


def repair_task(task, config, connection=None):
    from vericode.hosted_provider import use_connection
    controller = {"direct": record_direct_task, "feedback": record_feedback_task,
                  "augmented": record_augmented_task}[config.strategy]
    with use_connection(connection):
        return controller(task, config)


def evaluate_repair(data_root, repair):
    config = RunConfiguration.from_dict(repair["configuration"])
    return score_record(data_root, repair, config)


def cleanup_unconfirmed(value):
    if isinstance(value, dict):
        return value.get("cleanup_confirmed") is False or any(cleanup_unconfirmed(v) for v in value.values())
    if isinstance(value, list):
        return any(cleanup_unconfirmed(v) for v in value)
    return False
