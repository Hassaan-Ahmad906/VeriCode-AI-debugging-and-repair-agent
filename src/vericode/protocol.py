"""Freeze identities and offline budgets before demonstration collection."""

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import UUID, uuid4

from vericode.batch import runtime_fingerprint
from vericode.benchmark import verify_repair_freeze
from vericode.checkpoints import fingerprint
from vericode.datasets import TaskManifest, read_json
from vericode.docker_executor import DockerExecutor
from vericode.experiments import _git_revision
from vericode.model_io import identifier
from vericode.run_config import RunConfiguration
from vericode.schemas import ValidationError, require_fields, require_id, require_text, require_version

STRATEGIES = ("direct", "feedback", "augmented")


def study_config(data: dict) -> dict[str, RunConfiguration]:
    data = require_fields(data, {"schema_version", "label", "paid_api_enabled", "spending_cap_usd", "random_seed", "strategies"}, "study configuration")
    require_version(data["schema_version"])
    identifier(data["label"], "study label")
    if data["paid_api_enabled"] is not False or type(data["spending_cap_usd"]) not in (int, float) or data["spending_cap_usd"] != 0:
        raise ValidationError("only an explicitly zero-cost offline study is implemented; paid adapters are disabled")
    if data["random_seed"] is not None:
        raise ValidationError("random_seed: no seeded live adapter is implemented; use null")
    configs = require_fields(data["strategies"], set(STRATEGIES), "study strategies")
    parsed = {name: RunConfiguration.from_dict(configs[name]) for name in STRATEGIES}
    direct = parsed["direct"]
    if any(config.provider != "mock" for config in parsed.values()):
        raise ValidationError("frozen demonstration studies require mock providers; local models need a separate measured protocol")
    for name, config in parsed.items():
        if config.strategy != name:
            raise ValidationError("study strategy/configuration mismatch")
        if (config.backend, config.provider, config.model, config.image, config.execution, config.generation) != (
            direct.backend, direct.provider, direct.model, direct.image, direct.execution, direct.generation
        ):
            raise ValidationError("study requires the same provider/model, sandbox and per-response generation limits for all strategies")
    return parsed


def freeze_protocol(data_root: Path, configuration: dict, split: str) -> dict:
    configs = study_config(configuration)
    if split not in ("development", "final"):
        raise ValidationError("study split: expected development or final")
    repair_freeze = verify_repair_freeze(data_root)
    manifest = TaskManifest.load(data_root / f"manifests/{split}.json")
    tasks = manifest.load_tasks(data_root / "repair")
    if not 1 <= len(tasks) <= 100:
        raise ValidationError("study requires 1-100 fixed tasks")
    git_commit = _git_revision()
    if git_commit is None:
        raise ValidationError("study requires a recorded Git HEAD")
    config = configs["direct"]
    image_id = DockerExecutor(config.image, config.execution).prepare() if config.backend == "docker" else None
    protocol = {
        "schema_version": 1, "protocol_id": str(uuid4()), "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": configuration, "run_kind": "mock" if config.backend == "mock" else "sandbox_smoke",
        "split": split, "manifest": asdict(manifest),
        "task_fingerprints": {task.task_id: fingerprint(asdict(task)) for task in tasks},
        "repair_freeze_sha256": fingerprint(repair_freeze),
        "evaluation_freeze_sha256": fingerprint(read_json(data_root / "benchmark/evaluation_freeze.json")),
        "runtime": runtime_fingerprint(), "git_commit": git_commit, "docker_image_id": image_id,
        "prompt_versions": {"direct": "repair-v1", "feedback": "feedback-v1", "test_generation": "test-cases-v1", "oracle": "spec-rules-v2"},
        "claims": {"measured_llm_results_available": False, "compute_matched": False,
                   "collection": "pipeline demonstration with scripted development repairs and unchanged final-task mocks"},
    }
    protocol["protocol_sha256"] = fingerprint(protocol)
    return protocol


def validate_protocol(protocol: dict) -> dict[str, RunConfiguration]:
    protocol = require_fields(protocol, {"schema_version", "protocol_id", "created_at_utc", "configuration", "run_kind", "split", "manifest",
                               "task_fingerprints", "repair_freeze_sha256", "evaluation_freeze_sha256", "runtime", "git_commit",
                               "docker_image_id", "prompt_versions", "claims", "protocol_sha256"}, "frozen protocol")
    require_version(protocol["schema_version"])
    if protocol["protocol_sha256"] != fingerprint({k: v for k, v in protocol.items() if k != "protocol_sha256"}):
        raise ValidationError("frozen protocol checksum mismatch")
    configs = study_config(protocol["configuration"])
    if protocol["split"] not in ("development", "final"):
        raise ValidationError("frozen protocol has an invalid split")
    manifest = require_fields(protocol["manifest"], set(TaskManifest.__dataclass_fields__), "frozen manifest")
    require_version(manifest["schema_version"])
    require_text(manifest["dataset_version"], "frozen dataset version")
    ids = manifest["task_ids"]
    if manifest["split"] != protocol["split"] or not isinstance(ids, (list, tuple)) or not 1 <= len(ids) <= 100:
        raise ValidationError("frozen manifest split/task list is invalid")
    for task_id in ids:
        require_id(task_id)
    if len(set(ids)) != len(ids) or set(protocol["task_fingerprints"]) != set(ids):
        raise ValidationError("frozen manifest has duplicate/mismatched task identities")
    digests = [protocol["repair_freeze_sha256"], protocol["evaluation_freeze_sha256"], *protocol["task_fingerprints"].values()]
    if any(not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value) for value in digests):
        raise ValidationError("frozen protocol contains invalid fingerprints")
    try:
        UUID(protocol["protocol_id"])
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("frozen protocol ID is invalid") from None
    if not isinstance(protocol["git_commit"], str) or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", protocol["git_commit"]):
        raise ValidationError("frozen Git revision is invalid")
    image = protocol["docker_image_id"]
    if configs["direct"].backend == "docker" and (not isinstance(image, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", image)):
        raise ValidationError("frozen Docker image must be an immutable ID")
    if configs["direct"].backend == "mock" and image is not None:
        raise ValidationError("mock protocol cannot claim a measured Docker image")
    expected_kind = "mock" if configs["direct"].backend == "mock" else "sandbox_smoke"
    if protocol["run_kind"] != expected_kind or protocol["claims"].get("measured_llm_results_available") is not False or protocol["claims"].get("compute_matched") is not False:
        raise ValidationError("offline protocol has incompatible measurement claims")
    return configs


def verify_collection_inputs(data_root: Path, protocol: dict) -> tuple:
    validate_protocol(protocol)
    if runtime_fingerprint() != protocol["runtime"]:
        raise ValidationError("frozen runtime changed; preserve the old study and freeze a new protocol")
    if fingerprint(verify_repair_freeze(data_root)) != protocol["repair_freeze_sha256"]:
        raise ValidationError("repair freeze changed")
    if fingerprint(read_json(data_root / "benchmark/evaluation_freeze.json")) != protocol["evaluation_freeze_sha256"]:
        raise ValidationError("evaluation identity changed")
    manifest = TaskManifest.load(data_root / f"manifests/{protocol['split']}.json")
    tasks = manifest.load_tasks(data_root / "repair")
    if fingerprint(asdict(manifest)) != fingerprint(protocol["manifest"]) or {
        task.task_id: fingerprint(asdict(task)) for task in tasks
    } != protocol["task_fingerprints"]:
        raise ValidationError("frozen manifest/task inputs changed")
    return tasks
