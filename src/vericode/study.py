"""Two-phase, resumable demonstration collection with no evaluator feedback."""

from pathlib import Path

from vericode.augmented import record_augmented_task
from vericode.checkpoints import Checkpoint, fingerprint, locked_directory
from vericode.direct_run import make_executor, record_direct_task
from vericode.docker_executor import DockerExecutor
from vericode.feedback_run import record_feedback_task
from vericode.metrics import evaluation_metrics
from vericode.model_io import Usage, CallRecord, summarize_calls
from vericode.protocol import STRATEGIES, validate_protocol, verify_collection_inputs
from vericode.records import read_record
from vericode.scoring import score_record
from vericode.schemas import ValidationError, require_fields


def study_keys(protocol):
    return tuple(f"{phase}__{strategy}__{task_id}" for phase in ("repair", "score")
                 for strategy in STRATEGIES for task_id in protocol["manifest"]["task_ids"])


def _unsafe_cleanup(record, backend):
    if backend != "docker" or record["payload"]["status"] != "infrastructure_error":
        return False
    payload = record["payload"]
    executions = [payload.get(key) for key in ("initial_execution", "repair_execution", "baseline_execution", "candidate_execution")]
    executions = [result for result in executions if result is not None]
    return not executions or any(result.get("cleanup_confirmed") is not True for result in executions)


def study_summary(protocol, records, newly_completed):
    repairs = [record["payload"] for record in records.values() if record["phase"] == "repair"]
    scores = [record["payload"] for record in records.values() if record["phase"] == "score"]
    calls = []
    for repair in repairs:
        for raw in repair["model_calls"]:
            values = {key: raw[key] for key in CallRecord.__dataclass_fields__ if key != "usage"}
            calls.append(CallRecord(**values, usage=Usage(**raw["usage"])))
    expected = len(protocol["manifest"]["task_ids"]) * len(STRATEGIES)
    return {"schema_version": 1, "protocol_id": protocol["protocol_id"], "protocol_sha256": protocol["protocol_sha256"],
            "run_kind": protocol["run_kind"], "measured_llm_results_available": False,
            "expected_repairs": expected, "completed_repairs": len(repairs), "completed_scores": len(scores),
            "pending": 2 * expected - len(records), "newly_completed": newly_completed,
            "usage": summarize_calls(tuple(calls)), "evaluation": evaluation_metrics(scores)}


def load_study(directory: Path):
    metadata = read_record(directory / "batch.json")
    protocol = metadata["identity"]["protocol"]
    validate_protocol(protocol)
    checkpoint = Checkpoint(directory, {"protocol": protocol}, resume=True)
    records = checkpoint.completed(study_keys(protocol))
    _validate_records(protocol, records)
    return protocol, records


def _validate_records(protocol, records):
    configs = validate_protocol(protocol)
    repair_keys = {key for key in study_keys(protocol) if key.startswith("repair__")}
    for key, record in records.items():
        require_fields(record, {"task_id", "phase", "payload"}, "study outcome")
        if record["task_id"] != key or record.get("phase") not in ("repair", "score") or not isinstance(record.get("payload"), dict):
            raise ValidationError("study journal contains incompatible outcomes")
        phase, strategy, task_id = key.split("__", 2)
        if (record["phase"] != phase or record["payload"].get("strategy") != strategy or record["payload"].get("task_id") != task_id):
            raise ValidationError("study outcome identity mismatch")
        payload = record["payload"]
        if phase == "repair":
            budget = configs[strategy].generation.max_transport_calls if strategy == "direct" else configs[strategy].feedback.max_model_calls
            calls = payload.get("model_calls")
            if (payload.get("configuration") != configs[strategy].to_dict() or not isinstance(calls, list)
                or len(calls) > budget or payload.get("usage", {}).get("model_calls") != len(calls)
                or [call.get("call_index") for call in calls] != list(range(1, len(calls) + 1))):
                raise ValidationError("study repair configuration/call accounting mismatch")
        else:
            if not repair_keys.issubset(records):
                raise ValidationError("study scored before all repairs were durably completed")
            repair = records[f"repair__{strategy}__{task_id}"]["payload"]
            if payload.get("repair_record_sha256") != fingerprint(repair) or payload.get("repair_run_id") != repair.get("run_id"):
                raise ValidationError("study score does not link to its exact repair record")


def run_study(data_root: Path, protocol: dict, directory: Path, *, resume=False):
    configs = validate_protocol(protocol)
    tasks = verify_collection_inputs(data_root, protocol)
    config = configs["direct"]
    with locked_directory(directory, resume=resume):
        checkpoint = Checkpoint(directory, {"protocol": protocol}, resume=resume, image_id=protocol["docker_image_id"])
        records = checkpoint.completed(study_keys(protocol))
        _validate_records(protocol, records)
        original_count = len(records)
        if any(_unsafe_cleanup(record, config.backend) for record in records.values()):
            raise ValidationError("study has unconfirmed Docker cleanup; resolve it before pending work")
        executor = None

        def get_executor():
            nonlocal executor
            if executor is None:
                if config.backend == "docker":
                    executor = DockerExecutor(protocol["docker_image_id"], config.execution)
                    if executor.prepare() != protocol["docker_image_id"]:
                        raise ValidationError("frozen Docker image is unavailable")
                else:
                    executor = make_executor(config)
            return executor

        for phase in ("repair", "score"):
            # Finish every repair before opening any evaluator suite.
            for strategy in STRATEGIES:
                for task in tasks:
                    key = f"{phase}__{strategy}__{task.task_id}"
                    if key in records:
                        continue
                    get_executor()  # Preflight before any durable start/model call.
                    started = checkpoint.start(key)
                    if phase == "repair":
                        controller = {"direct": record_direct_task, "feedback": record_feedback_task, "augmented": record_augmented_task}[strategy]
                        payload = controller(task, configs[strategy], executor)
                    else:
                        repair = records[f"repair__{strategy}__{task.task_id}"]["payload"]
                        payload = score_record(data_root, repair, config, executor)
                    record = {"task_id": key, "phase": phase, "payload": payload}
                    checkpoint.finish(started, record)
                    records[key] = record
                    if payload["status"] == "infrastructure_error":
                        return study_summary(protocol, records, len(records) - original_count)
        return study_summary(protocol, records, len(records) - original_count)
