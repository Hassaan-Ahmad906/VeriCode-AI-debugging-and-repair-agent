"""Validated repair inputs. These objects never contain evaluator assets."""

from dataclasses import dataclass
import re
from typing import Any

SCHEMA_VERSION = 1
MAX_TEXT_BYTES = 32_768


class ValidationError(ValueError):
    """A task or model response violates the supported data contract."""


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field}: expected a non-empty string")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ValidationError(f"{field}: text must be valid UTF-8") from exc
    if size > MAX_TEXT_BYTES:
        raise ValidationError(f"{field}: exceeds {MAX_TEXT_BYTES} UTF-8 bytes")
    if "\x00" in value:
        raise ValidationError(f"{field}: NUL characters are forbidden")
    return value


def require_id(value: Any, field: str = "task_id") -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value):
        raise ValidationError(f"{field}: expected a lowercase identifier (1-64 characters)")
    return value


def require_version(value: Any) -> None:
    if type(value) is not int or value != SCHEMA_VERSION:
        raise ValidationError(f"schema_version: expected {SCHEMA_VERSION}")


def require_fields(data: Any, fields: set[str], context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError(f"{context}: expected a JSON object")
    missing = fields - data.keys()
    extra = data.keys() - fields
    if missing or extra:
        raise ValidationError(
            f"{context}: missing fields {sorted(missing)}; unknown fields {sorted(extra)}"
        )
    return data


@dataclass(frozen=True)
class RepairTask:
    schema_version: int
    dataset_version: str
    task_id: str
    split: str
    specification: str
    entry_point: str
    task_file: str
    source: str
    repair_tests: str

    def __post_init__(self) -> None:
        require_version(self.schema_version)
        require_id(self.task_id)
        require_text(self.dataset_version, "dataset_version")
        if self.split not in ("development", "final"):
            raise ValidationError("split: expected 'development' or 'final'")
        require_id(self.entry_point, "entry_point")
        # One canonical target eliminates platform-specific path interpretation.
        if self.task_file != "solution.py":
            raise ValidationError("task_file: only 'solution.py' is permitted")
        for field in ("specification", "source", "repair_tests"):
            require_text(getattr(self, field), field)

    @classmethod
    def from_dict(cls, data: Any) -> "RepairTask":
        return cls(**require_fields(data, set(cls.__dataclass_fields__), "task"))


@dataclass(frozen=True)
class Candidate:
    """A full-file replacement proposal, not an instruction to run code."""

    task_id: str
    target_file: str
    replacement_source: str

    def __post_init__(self) -> None:
        require_id(self.task_id)
        if self.target_file != "solution.py":
            raise ValidationError("target_file: only 'solution.py' is permitted")
        require_text(self.replacement_source, "replacement_source")

    @classmethod
    def from_dict(cls, data: Any) -> "Candidate":
        return cls(**require_fields(data, set(cls.__dataclass_fields__), "candidate"))
