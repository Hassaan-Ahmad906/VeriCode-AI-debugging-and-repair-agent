"""Fixed-manifest repair batches with conservative resumption."""

from dataclasses import asdict
import hashlib
import math
from pathlib import Path
import platform

from vericode.checkpoints import Checkpoint, fingerprint, locked_directory
from vericode.datasets import TaskManifest
from vericode.direct_run import make_executor, record_direct_task
from vericode.feedback_run import record_feedback_task
from vericode.augmented import record_augmented_task
from vericode.docker_executor import DockerExecutor
from vericode.experiments import _git_revision
from vericode.run_config import RunConfiguration
from vericode.schemas import ValidationError


def runtime_fingerprint() -> dict:
    package = Path(__file__).resolve().parent
    repository = package.parents[1]
    files = sorted(package.rglob("*.py"))
    files += [path for path in [repository / "pyproject.toml", *(repository / "sandbox").glob("*")]
              if path.is_file() and path.name in {"pyproject.toml", "Dockerfile", ".dockerignore", "runner.py", "pytest.ini", "requirements.txt"}]
    digest = hashlib.sha256()
    for path in sorted(files):
        name = str(path.relative_to(repository)).replace("\\", "/").encode()
        content = path.read_bytes()
        digest.update(len(name).to_bytes(4, "big") + name + len(content).to_bytes(8, "big") + content)
    return {"python_version": platform.python_version(), "platform": platform.system(), "workspace_sha256": digest.hexdigest()}


def _unconfirmed_cleanup(record: dict, config: RunConfiguration) -> bool:
    if config.backend != "docker" or record["status"] != "infrastructure_error":
        return False
    execution = record.get("repair_execution")
    return execution is None or execution.get("cleanup_confirmed") is False


def _summary(checkpoint: Checkpoint, records: dict, total: int, skipped: int) -> dict:
    outcomes = {}
    for record in records.values():
        outcomes[record["status"]] = outcomes.get(record["status"], 0) + 1
    usage = {"model_calls": sum(record["usage"]["model_calls"] for record in records.values())}
    for key in ("input_tokens", "output_tokens", "cost_usd"):
        values = [record["usage"][key] for record in records.values()]
        known = [record["usage"][f"known_{key}"] for record in records.values()]
        usage[key] = (math.fsum(values) if key == "cost_usd" else sum(values)) if all(value is not None for value in values) else None
        usage[f"known_{key}"] = math.fsum(known) if key == "cost_usd" else sum(known)
    return {"schema_version": 1, "batch_id": checkpoint.batch_id,
            "strategy": checkpoint.metadata["identity"]["configuration"]["strategy"],
            "run_kind": "mock" if checkpoint.metadata["identity"]["configuration"]["backend"] == "mock" else "sandbox_smoke",
            "task_count": total, "completed": len(records), "newly_completed": len(records) - skipped,
            "skipped_completed": skipped, "pending": total - len(records), "outcomes": outcomes,
            "usage": usage, "journal": str(checkpoint.journal), "evaluation": None}


def run_batch(data_root: Path, manifest_path: Path, config: RunConfiguration, directory: Path,
              *, resume: bool = False) -> dict:
    manifest = TaskManifest.load(manifest_path)
    if manifest.split != "development" or not 1 <= len(manifest.task_ids) <= 100:
        raise ValidationError("mock batch requires a development manifest with 1-100 fixed tasks")
    tasks = manifest.load_tasks(data_root / "repair")
    identity = {"configuration": config.to_dict(), "manifest": asdict(manifest),
                "task_fingerprints": {task.task_id: fingerprint(asdict(task)) for task in tasks},
                "runtime": runtime_fingerprint(), "random_seed": None}
    with locked_directory(directory, resume=resume):
        executor = None
        image_id = None
        if not resume and config.backend == "docker":
            executor = make_executor(config)
            image_id = executor.prepare()
        checkpoint = Checkpoint(directory, identity, resume=resume, image_id=image_id)
        records = checkpoint.completed(manifest.task_ids)
        for task_id, record in records.items():
            if (record.get("configuration") != config.to_dict() or record.get("strategy") != config.strategy
                or record.get("schema_version") != config.to_dict()["schema_version"]):
                raise ValidationError(f"saved outcome for {task_id} has incompatible configuration")
            if _unconfirmed_cleanup(record, config):
                raise ValidationError(f"saved Docker cleanup for {task_id} is unconfirmed; resolve it before further jobs")
        skipped = len(records)
        pending = [task for task in tasks if task.task_id not in records]
        if pending and executor is None:
            executor = make_executor(config)
        if pending and config.backend == "docker":
            # Resume uses the recorded immutable image, even if its tag has moved.
            image_id = checkpoint.metadata["docker_image_id"]
            if not isinstance(image_id, str) or not image_id.startswith("sha256:"):
                raise ValidationError("batch has no recorded immutable Docker image")
            executor = DockerExecutor(image_id, config.execution)
            if executor.prepare() != image_id:
                raise ValidationError("recorded Docker image is unavailable or mismatched")
        for task in pending:
            started = checkpoint.start(task.task_id)  # fsync before any model call.
            controller = {"direct": record_direct_task, "feedback": record_feedback_task,
                          "augmented": record_augmented_task}[config.strategy]
            record = controller(task, config, executor)
            record["batch_id"] = checkpoint.batch_id
            record["runtime"] = identity["runtime"]
            checkpoint.finish(started, record)  # Terminal failures are outcomes too.
            records[task.task_id] = record
            if record["status"] == "infrastructure_error":
                break
        result = _summary(checkpoint, records, len(tasks), skipped)
        result["git_commit"] = _git_revision()
        return result
