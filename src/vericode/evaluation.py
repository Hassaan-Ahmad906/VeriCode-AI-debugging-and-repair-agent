"""Evaluator-only input loading. Never pass these objects to the repair provider."""

from dataclasses import dataclass
from pathlib import Path

from vericode.datasets import contained_file, read_json
from vericode.schemas import (
    ValidationError, require_fields, require_id, require_text, require_version,
)


@dataclass(frozen=True)
class EvaluationSuite:
    schema_version: int
    dataset_version: str
    task_id: str
    tests: str

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        require_id(self.task_id)
        require_text(self.dataset_version, "dataset_version")
        require_text(self.tests, "evaluation tests")


def load_evaluation_suite(evaluation_root: Path, task_id: str) -> EvaluationSuite:
    data = read_json(contained_file(evaluation_root, task_id, "suite.json"))
    suite = EvaluationSuite(**require_fields(data, set(EvaluationSuite.__dataclass_fields__), "suite"))
    if suite.task_id != task_id:
        raise ValidationError(f"evaluation task_id: expected {task_id!r}")
    return suite
