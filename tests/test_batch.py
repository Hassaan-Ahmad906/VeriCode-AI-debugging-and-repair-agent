from dataclasses import replace
import json
import shutil

import pytest

from vericode import batch
from vericode.checkpoints import Checkpoint, locked_directory
from vericode.cli import main
from vericode.run_config import RunConfiguration
from vericode.results import ExecutionResult
from vericode.schemas import ValidationError


@pytest.fixture
def copied_data(data_root, tmp_path):
    root = tmp_path / "dataset"
    shutil.copytree(data_root, root)
    return root


def run(root, directory, **kwargs):
    return batch.run_batch(root, root / "manifests/development.json", kwargs.pop("config", RunConfiguration()), directory, **kwargs)


def events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def test_fresh_batch_and_resume_preserve_exact_completed_bytes(copied_data, tmp_path, monkeypatch):
    directory = tmp_path / "run"
    first = run(copied_data, directory)
    before = (directory / "events.jsonl").read_bytes()
    assert first["completed"] == first["newly_completed"] == first["usage"]["model_calls"] == 3
    assert first["outcomes"] == {"candidate_ready": 3}

    def forbidden(*args, **kwargs):
        pytest.fail("completed tasks must not invoke repair again")

    monkeypatch.setattr(batch, "record_direct_task", forbidden)
    resumed = run(copied_data, directory, resume=True)
    assert resumed["newly_completed"] == 0 and resumed["skipped_completed"] == 3
    assert resumed["usage"] == first["usage"]
    assert (directory / "events.jsonl").read_bytes() == before
    assert not (directory / ".lock").exists()


def test_resume_runs_only_tasks_not_yet_started(copied_data, tmp_path, monkeypatch):
    directory = tmp_path / "run"
    original = Checkpoint.start
    count = 0

    def stop_before_second_start(self, task_id):
        nonlocal count
        count += 1
        if count == 2:
            raise KeyboardInterrupt("trusted between-task interruption")
        return original(self, task_id)

    monkeypatch.setattr(Checkpoint, "start", stop_before_second_start)
    with pytest.raises(KeyboardInterrupt):
        run(copied_data, directory)
    assert len(events(directory)) == 2
    monkeypatch.setattr(Checkpoint, "start", original)
    resumed = run(copied_data, directory, resume=True)
    assert resumed["skipped_completed"] == 1 and resumed["newly_completed"] == 2
    assert resumed["usage"]["model_calls"] == 3
    assert len(events(directory)) == 6


def test_uncertain_started_call_is_never_automatically_replayed(copied_data, tmp_path, monkeypatch):
    directory = tmp_path / "run"

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt("possible call already sent")

    monkeypatch.setattr(batch, "record_direct_task", interrupted)
    with pytest.raises(KeyboardInterrupt):
        run(copied_data, directory)
    before = (directory / "events.jsonl").read_bytes()
    with pytest.raises(ValidationError, match="uncertain started outcome"):
        run(copied_data, directory, resume=True)
    assert (directory / "events.jsonl").read_bytes() == before
    assert not (directory / ".lock").exists()


@pytest.mark.parametrize("change", ["config", "task", "manifest", "runtime"])
def test_resume_rejects_changed_experiment_inputs(copied_data, tmp_path, monkeypatch, change):
    directory = tmp_path / "run"
    run(copied_data, directory)
    config = RunConfiguration()
    if change == "config":
        config = replace(config, model="another-mock-label")
    elif change == "task":
        path = copied_data / "repair/clamp/task.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["source"] += "# changed input\n"
        path.write_text(json.dumps(data), encoding="utf-8")
    elif change == "manifest":
        path = copied_data / "manifests/development.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["task_ids"].reverse()
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        monkeypatch.setattr(batch, "runtime_fingerprint", lambda: {"workspace_sha256": "changed"})
    before = (directory / "events.jsonl").read_bytes()
    with pytest.raises(ValidationError, match="changed"):
        run(copied_data, directory, config=config, resume=True)
    assert (directory / "events.jsonl").read_bytes() == before


@pytest.mark.parametrize("corruption", ["torn", "duplicate", "checksum", "header"])
def test_corrupt_checkpoint_is_rejected_without_new_calls(copied_data, tmp_path, corruption):
    directory = tmp_path / "run"
    run(copied_data, directory)
    journal = directory / "events.jsonl"
    lines = journal.read_bytes().splitlines(keepends=True)
    if corruption == "torn":
        journal.write_bytes(b"".join(lines)[:-1])
    elif corruption == "duplicate":
        journal.write_bytes(b"".join(lines + lines[:2]))
    elif corruption == "checksum":
        record = json.loads(lines[1])
        record["record"]["status"] = "changed"
        lines[1] = json.dumps(record).encode() + b"\n"
        journal.write_bytes(b"".join(lines))
    else:
        path = directory / "batch.json"
        header = json.loads(path.read_text(encoding="utf-8"))
        header["docker_image_id"] = "changed"
        path.write_text(json.dumps(header), encoding="utf-8")
    before = journal.read_bytes()
    with pytest.raises(ValidationError):
        run(copied_data, directory, resume=True)
    assert journal.read_bytes() == before


def test_directory_lock_blocks_concurrent_controller_without_removing_its_lock(tmp_path):
    directory = tmp_path / "locked"
    with locked_directory(directory, resume=False):
        before = (directory / ".lock").read_bytes()
        with pytest.raises(ValidationError, match="locked"):
            with locked_directory(directory, resume=True):
                pytest.fail("second controller must not enter")
        assert (directory / ".lock").read_bytes() == before
    assert not (directory / ".lock").exists()


def test_existing_user_directory_is_preserved(copied_data, tmp_path):
    directory = tmp_path / "user-work"
    directory.mkdir()
    path = directory / "important.txt"
    path.write_text("preserve", encoding="utf-8")
    with pytest.raises(ValidationError, match="not empty"):
        run(copied_data, directory)
    assert list(directory.iterdir()) == [path]
    assert path.read_text(encoding="utf-8") == "preserve"


def test_terminal_failure_is_skipped_on_resume(copied_data, tmp_path, monkeypatch):
    original = batch.record_direct_task

    def fail_one(task, *args, **kwargs):
        record = original(task, *args, **kwargs)
        if task.task_id == "clamp":
            record["status"] = "invalid_patch"
            record["agent_accepted"] = False
        return record

    monkeypatch.setattr(batch, "record_direct_task", fail_one)
    directory = tmp_path / "run"
    result = run(copied_data, directory)
    assert result["outcomes"]["invalid_patch"] == 1
    monkeypatch.setattr(batch, "record_direct_task", lambda *a, **k: pytest.fail("must not rerun"))
    resumed = run(copied_data, directory, resume=True)
    assert resumed["newly_completed"] == 0 and resumed["outcomes"] == result["outcomes"]


def test_batch_cli_config_and_resume(copied_data, tmp_path, capsys):
    config = tmp_path / "config.json"
    config.write_text(json.dumps(RunConfiguration().to_dict()), encoding="utf-8")
    directory = tmp_path / "cli-run"
    args = ["batch", "--config", str(config), "--manifest", str(copied_data / "manifests/development.json"),
            "--data-root", str(copied_data), "--run-dir", str(directory)]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["newly_completed"] == 3
    assert main(args + ["--resume"]) == 0
    assert json.loads(capsys.readouterr().out)["newly_completed"] == 0


def test_infrastructure_failure_halts_batch_and_is_not_replayed(copied_data, tmp_path, monkeypatch):
    original = batch.record_direct_task
    count = 0

    def infrastructure(task, *args, **kwargs):
        nonlocal count
        count += 1
        record = original(task, *args, **kwargs)
        record["status"] = "infrastructure_error"
        return record

    monkeypatch.setattr(batch, "record_direct_task", infrastructure)
    directory = tmp_path / "run"
    result = run(copied_data, directory)
    assert count == 1 and result["completed"] == 1 and result["pending"] == 2
    monkeypatch.setattr(batch, "record_direct_task", original)
    resumed = run(copied_data, directory, resume=True)
    assert resumed["skipped_completed"] == 1 and resumed["newly_completed"] == 2
    assert resumed["outcomes"] == {"infrastructure_error": 1, "candidate_ready": 2}


def test_unconfirmed_docker_cleanup_blocks_resume_before_more_calls(copied_data, tmp_path, monkeypatch):
    class FakeDocker:
        def __init__(self, *args, **kwargs):
            pass

        def prepare(self):
            return "sha256:" + "a" * 64

        def run(self, source, tests):
            return ExecutionResult("sandbox", "infrastructure_error", cleanup_confirmed=False,
                                   job_name="vericode-job-test", detail="Simulated unconfirmed cleanup.")

    monkeypatch.setattr(batch, "make_executor", lambda config: FakeDocker())
    monkeypatch.setattr(batch, "DockerExecutor", FakeDocker)
    directory = tmp_path / "run"
    config = RunConfiguration(backend="docker")
    result = run(copied_data, directory, config=config)
    assert result["pending"] == 2
    before = (directory / "events.jsonl").read_bytes()
    with pytest.raises(ValidationError, match="cleanup.*unconfirmed"):
        run(copied_data, directory, config=config, resume=True)
    assert (directory / "events.jsonl").read_bytes() == before


def test_storage_budget_stops_before_any_model_call(copied_data, tmp_path, monkeypatch):
    monkeypatch.setattr("vericode.checkpoints.MAX_JOURNAL_BYTES", 1000)
    monkeypatch.setattr(batch, "record_direct_task", lambda *a, **k: pytest.fail("must not send a call without log capacity"))
    directory = tmp_path / "run"
    with pytest.raises(ValidationError, match="storage budget.*before task start"):
        run(copied_data, directory)
    assert events(directory) == []


@pytest.mark.docker
def test_docker_batch_freezes_image_and_resume_needs_no_docker(copied_data, tmp_path, monkeypatch):
    config = RunConfiguration(backend="docker")
    directory = tmp_path / "docker-run"
    result = run(copied_data, directory, config=config)
    header = json.loads((directory / "batch.json").read_text(encoding="utf-8"))
    records = [event["record"] for event in events(directory) if event["event"] == "completed"]
    assert result["outcomes"] == {"visible_passed": 3}, [(record["detail"], record["repair_execution"]) for record in records]
    assert all(record["repair_execution"]["image_id"] == header["docker_image_id"] for record in records)
    assert all(record["repair_execution"]["cleanup_confirmed"] is True for record in records)
    assert all(record["evaluation"] is None for record in records)
    monkeypatch.setattr(batch, "make_executor", lambda *a, **k: pytest.fail("completed resume needs no Docker"))
    resumed = run(copied_data, directory, config=config, resume=True)
    assert resumed["skipped_completed"] == 3 and resumed["newly_completed"] == 0
