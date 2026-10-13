"""Durable append-only batch checkpoints; never silently replay uncertain calls."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from vericode.datasets import _unique_object
from vericode.schemas import ValidationError, require_fields, require_version

MAX_LINE_BYTES = 16 * 1024 * 1024  # B retains up to ten bounded request/execution pairs.
MAX_JOURNAL_BYTES = 64 * 1024 * 1024


def canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("utf-8")


def fingerprint(value) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _nonfinite(value):
    raise ValidationError("checkpoint contains a non-finite JSON value")


def decode_json(raw: bytes):
    try:
        return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_nonfinite)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError("checkpoint JSON is malformed; preserve the existing files") from exc


def _regular_path(path: Path) -> None:
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        raise ValidationError(f"checkpoint path must not be a link: {path.name}")


@contextmanager
def locked_directory(directory: Path, *, resume: bool):
    _regular_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if not resume and any(directory.iterdir()):
        raise ValidationError("run directory is not empty; use --resume or a new directory")
    for name in ("batch.json", "events.jsonl", ".lock"):
        _regular_path(directory / name)
    lock = directory / ".lock"
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError:
        raise ValidationError("batch is locked; confirm the previous controller has stopped before recovering its lock") from None
    try:
        with stream:
            json.dump({"pid": os.getpid(), "lock_id": str(uuid4())}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        yield
    finally:
        lock.unlink(missing_ok=True)


class Checkpoint:
    def __init__(self, directory: Path, identity: dict, *, resume: bool, image_id: str | None = None):
        self.directory = directory
        self.journal = directory / "events.jsonl"
        metadata_path = directory / "batch.json"
        expected = fingerprint(identity)
        if resume:
            with metadata_path.open("rb") as stream:
                raw = stream.read(MAX_LINE_BYTES + 1)
            if len(raw) > MAX_LINE_BYTES:
                raise ValidationError("batch metadata exceeds its size limit")
            metadata = require_fields(decode_json(raw), {
                "schema_version", "batch_id", "created_at_utc", "identity", "fingerprint", "docker_image_id", "header_sha256"
            }, "batch metadata")
            require_version(metadata["schema_version"])
            if metadata["header_sha256"] != fingerprint({key: value for key, value in metadata.items() if key != "header_sha256"}):
                raise ValidationError("batch metadata checksum does not match; preserve the existing files")
            if fingerprint(metadata["identity"]) != metadata["fingerprint"] or metadata["fingerprint"] != expected:
                raise ValidationError("resume inputs/configuration/runtime changed; preserve this batch and use a new directory")
            if not self.journal.is_file():
                raise ValidationError("batch journal is missing; initialization may have been interrupted")
            self.metadata = metadata
        else:
            self.metadata = {
                "schema_version": 1, "batch_id": str(uuid4()),
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "identity": identity, "fingerprint": expected, "docker_image_id": image_id,
            }
            self.metadata["header_sha256"] = fingerprint(self.metadata)
            with metadata_path.open("xb") as stream:
                stream.write(canonical_bytes(self.metadata) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            with self.journal.open("xb") as stream:
                stream.flush()
                os.fsync(stream.fileno())
        self.batch_id = self.metadata["batch_id"]

    def append(self, event: dict) -> None:
        payload = canonical_bytes(event) + b"\n"
        if len(payload) > MAX_LINE_BYTES or self.journal.stat().st_size + len(payload) > MAX_JOURNAL_BYTES:
            raise ValidationError("batch journal exceeds its configured storage bounds")
        with self.journal.open("ab") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

    def completed(self, task_ids: tuple[str, ...]) -> dict[str, dict]:
        if self.journal.stat().st_size > MAX_JOURNAL_BYTES:
            raise ValidationError("batch journal exceeds its size limit")
        records = {}
        pending = None
        seen = set()
        count = 0
        with self.journal.open("rb") as stream:
            while raw := stream.readline(MAX_LINE_BYTES + 1):
                count += 1
                if count > 2 * len(task_ids) or len(raw) > MAX_LINE_BYTES or not raw.endswith(b"\n"):
                    raise ValidationError("batch journal is oversized or has a torn line; preserve it before recovery")
                event = decode_json(raw)
                base = {"schema_version", "event", "batch_id", "task_id", "attempt_id", "created_at_utc"}
                kind = event.get("event") if isinstance(event, dict) else None
                fields = base if kind == "started" else base | {"record", "record_sha256"}
                event = require_fields(event, fields, "batch event")
                require_version(event["schema_version"])
                if event["batch_id"] != self.batch_id or event["task_id"] not in task_ids:
                    raise ValidationError("journal event does not match the frozen batch/task list")
                if kind == "started":
                    if pending is not None or event["task_id"] in seen:
                        raise ValidationError("journal contains overlapping or duplicate task starts")
                    seen.add(event["task_id"])
                    pending = event
                elif kind == "completed":
                    if pending is None or any(event[key] != pending[key] for key in ("task_id", "attempt_id")):
                        raise ValidationError("completed event has no matching task start")
                    record = event["record"]
                    if not isinstance(record, dict) or record.get("task_id") != event["task_id"] or fingerprint(record) != event["record_sha256"]:
                        raise ValidationError("completed record is corrupt or mismatched")
                    records[event["task_id"]] = record
                    pending = None
                else:
                    raise ValidationError("unsupported journal event")
        if pending is not None:
            raise ValidationError(f"task {pending['task_id']} has an uncertain started outcome; automatic replay is blocked")
        return records

    def start(self, task_id: str) -> dict:
        event = {"schema_version": 1, "event": "started", "batch_id": self.batch_id,
                 "task_id": task_id, "attempt_id": str(uuid4()),
                 "created_at_utc": datetime.now(timezone.utc).isoformat()}
        reserve = len(canonical_bytes(event)) + 1 + MAX_LINE_BYTES
        if self.journal.stat().st_size + reserve > MAX_JOURNAL_BYTES:
            raise ValidationError("journal storage budget exhausted before task start")
        self.append(event)
        return event

    def finish(self, started: dict, record: dict) -> None:
        self.append({**started, "event": "completed", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                     "record": record, "record_sha256": fingerprint(record)})
