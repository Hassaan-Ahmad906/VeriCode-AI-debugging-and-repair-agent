"""Bounded strict JSON readers for saved controller records."""

from pathlib import Path

from vericode.checkpoints import MAX_LINE_BYTES, decode_json
from vericode.schemas import ValidationError


def read_record(path: Path) -> dict:
    with path.open("rb") as stream:
        raw = stream.read(MAX_LINE_BYTES + 1)
    if len(raw) > MAX_LINE_BYTES:
        raise ValidationError("saved record exceeds the 16 MiB limit")
    value = decode_json(raw)
    if not isinstance(value, dict):
        raise ValidationError("saved record must be a JSON object")
    return value
