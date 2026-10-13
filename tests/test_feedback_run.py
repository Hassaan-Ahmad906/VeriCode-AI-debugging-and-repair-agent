from dataclasses import replace
import json
import shutil

import pytest

from vericode import batch
from vericode.checkpoints import Checkpoint, MAX_LINE_BYTES, canonical_bytes, locked_directory
from vericode.cli import main
from vericode.feedback import FeedbackLimits
from vericode.feedback_run import record_feedback_task, run_feedback
from vericode.datasets import load_task
from vericode.model_io import GenerationLimits
from vericode.results import ExecutionResult
from vericode.run_config import FeedbackConfiguration, RunConfiguration
from vericode.schemas import ValidationError

from test_feedback import FAILED, ScriptedExecutor, ScriptedTransport, provider, raw


def test_feedback_config_roundtrip_preserves_direct_schema():
    direct = RunConfiguration()
    feedback = FeedbackConfiguration()
    assert direct.to_dict()["schema_version"] == 1 and "feedback" not in direct.to_dict()
    assert feedback.to_dict()["schema_version"] == 2
    assert RunConfiguration.from_dict(feedback.to_dict()) == feedback
    changed = feedback.to_dict()
    changed["schema_version"] = 1
    with pytest.raises(ValidationError, match="schema_version 2"):
        RunConfiguration.from_dict(changed)


def test_feedback_cli_saves_complete_mock_history(data_root, tmp_path, capsys):
    output = tmp_path / "run.json"
    assert main(["feedback", "--data-root", str(data_root), "--output", str(output)]) == 0
    record = json.loads(capsys.readouterr().out)
    assert json.loads(output.read_text()) == record
    assert record["strategy"] == "feedback" and record["schema_version"] == 2
    assert record["status"] == "candidate_ready" and record["agent_accepted"] is None
    assert record["evaluation"] is None and record["paid_api_enabled"] is False
    assert record["usage"]["attempts"] == record["usage"]["model_calls"] == 1
    assert record["usage"]["cost_usd"] == 0
    assert record["initial_execution"]["status"] == "not_executed"
    assert len(record["attempt_history"]) == 1
    assert record["attempt_history"][0]["call_indices"] == [1]


def test_feedback_run_needs_no_evaluator_tree(data_root, tmp_path):
    shutil.copytree(data_root / "repair", tmp_path / "repair")
    shutil.copytree(data_root / "manifests", tmp_path / "manifests")
    record = run_feedback(tmp_path, "clamp", FeedbackConfiguration())
    assert record["evaluation"] is None and record["status"] == "candidate_ready"
    assert "evaluation" not in record["attempt_history"][0]["prompt"]


def test_feedback_batch_resume_adds_no_calls_and_rejects_changed_limits(data_root, tmp_path, monkeypatch):
    config = FeedbackConfiguration()
    directory = tmp_path / "batch"
    first = batch.run_batch(data_root, data_root / "manifests/development.json", config, directory)
    before = (directory / "events.jsonl").read_bytes()
    monkeypatch.setattr(batch, "record_feedback_task", lambda *a, **kw: pytest.fail("completed outcomes must be skipped"))
    second = batch.run_batch(data_root, data_root / "manifests/development.json", config, directory, resume=True)
    assert first["completed"] == second["completed"] == 3
    assert second["newly_completed"] == 0 and second["skipped_completed"] == 3
    assert second["usage"]["model_calls"] == 3
    assert (directory / "events.jsonl").read_bytes() == before
    changed = replace(config, feedback=FeedbackLimits(max_attempts=2))
    with pytest.raises(ValidationError, match="changed"):
        batch.run_batch(data_root, data_root / "manifests/development.json", changed, directory, resume=True)


@pytest.mark.parametrize("limits", [
    {"max_attempts": 0}, {"max_attempts": 11}, {"max_attempts": True},
    {"max_model_calls": 0}, {"max_model_calls": 31}, {"max_model_calls": 1.0},
    {"feedback_bytes": 255}, {"feedback_bytes": 16385},
])
def test_feedback_limits_reject_unbounded_or_ambiguous_values(limits):
    with pytest.raises(ValidationError):
        FeedbackLimits(**limits)


def test_cli_existing_output_stops_before_any_execution(tmp_path, monkeypatch):
    output = tmp_path / "existing.json"
    output.write_text("preserve", encoding="utf-8")
    monkeypatch.setattr("vericode.cli.run_feedback", lambda *a, **kw: pytest.fail("must not execute"))
    with pytest.raises(SystemExit) as error:
        main(["feedback", "--output", str(output)])
    assert error.value.code == 2 and output.read_text() == "preserve"


def test_cli_invalid_budget_stops_before_any_execution(monkeypatch):
    monkeypatch.setattr("vericode.cli.run_feedback", lambda *a, **kw: pytest.fail("must not execute"))
    with pytest.raises(SystemExit) as error:
        main(["feedback", "--max-model-calls", "0"])
    assert error.value.code == 2


def test_feedback_batch_uncertain_start_blocks_replay(data_root, tmp_path, monkeypatch):
    directory = tmp_path / "uncertain"
    config = FeedbackConfiguration()

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt("simulated crash after durable start")

    monkeypatch.setattr(batch, "record_feedback_task", interrupted)
    with pytest.raises(KeyboardInterrupt):
        batch.run_batch(data_root, data_root / "manifests/development.json", config, directory)
    before = (directory / "events.jsonl").read_bytes()
    monkeypatch.setattr(batch, "record_feedback_task", lambda *a, **kw: pytest.fail("uncertain work must not be replayed"))
    with pytest.raises(ValidationError, match="uncertain"):
        batch.run_batch(data_root, data_root / "manifests/development.json", config, directory, resume=True)
    assert (directory / "events.jsonl").read_bytes() == before


def test_initial_unconfirmed_cleanup_is_saved_and_blocks_pending_batch_work(data_root, tmp_path, monkeypatch):
    class UnavailableDocker:
        def __init__(self, *args):
            pass

        def prepare(self):
            return "sha256:" + "a" * 64

        def run(self, source, tests):
            return ExecutionResult("sandbox", "infrastructure_error", cleanup_confirmed=False)

    config = FeedbackConfiguration(backend="docker")
    directory = tmp_path / "unconfirmed"
    monkeypatch.setattr(batch, "make_executor", lambda config: UnavailableDocker())
    monkeypatch.setattr(batch, "DockerExecutor", UnavailableDocker)
    first = batch.run_batch(data_root, data_root / "manifests/development.json", config, directory)
    assert first["completed"] == 1 and first["pending"] == 2
    assert first["outcomes"] == {"infrastructure_error": 1} and first["usage"]["model_calls"] == 0
    monkeypatch.setattr(batch, "make_executor", lambda *args: pytest.fail("cleanup must be resolved first"))
    with pytest.raises(ValidationError, match="cleanup.*unconfirmed"):
        batch.run_batch(data_root, data_root / "manifests/development.json", config, directory, resume=True)


def test_environment_credentials_and_spending_cap_do_not_enable_paid_feedback(data_root, capsys, monkeypatch):
    monkeypatch.setenv("VERICODE_PROVIDER", "live-provider-not-implemented")
    monkeypatch.setenv("VERICODE_API_KEY", "credential-SENTINEL")
    monkeypatch.setenv("VERICODE_SPENDING_CAP_USD", "100")
    assert main(["feedback", "--data-root", str(data_root)]) == 0
    output = capsys.readouterr().out
    record = json.loads(output)
    assert "credential-SENTINEL" not in output
    assert record["paid_api_enabled"] is False and record["configuration"]["provider"] == "mock"
    assert record["usage"]["cost_usd"] == 0


def test_maximum_attempt_history_fits_reserved_journal_record(data_root, tmp_path, monkeypatch):
    # Stress actual serialized B history beyond the former 2 MiB record cap.
    # Observations are fixtures, and source strings are parsed but never executed.
    task = replace(load_task(data_root / "repair", "clamp"), specification="s" * 5000,
                   repair_tests="from solution import clamp\n#" + "t" * 5000 + "\n")
    sources = ["def clamp(value, lower, upper):\n    return lower\n#" + "\u2603" * 10000 + str(i) + "\n" for i in range(10)]
    transport = ScriptedTransport([raw(task, source) for source in sources])
    config = FeedbackConfiguration(generation=GenerationLimits(prompt_bytes=131072, response_bytes=131072),
                                   feedback=FeedbackLimits(max_attempts=10, max_model_calls=10, feedback_bytes=16384))
    controlled_provider = provider(transport)
    controlled_provider.limits = config.generation
    monkeypatch.setattr("vericode.feedback_run.MockProvider", lambda *args: controlled_provider)
    large = replace(FAILED, output="\U0001f600" * 16384, detail="\u00e9" * 16000)
    record = record_feedback_task(task, config, ScriptedExecutor([large] * 11))
    assert record["status"] == "attempt_budget_exhausted" and len(record["attempt_history"]) == 10
    size = len(canonical_bytes(record))
    assert 2 * 1024 * 1024 < size < MAX_LINE_BYTES
    directory = tmp_path / "large-history"
    with locked_directory(directory, resume=False):
        checkpoint = Checkpoint(directory, {"configuration": config.to_dict()}, resume=False, image_id=None)
        started = checkpoint.start(task.task_id)
        checkpoint.finish(started, record)
        recovered = checkpoint.completed((task.task_id,))
    assert recovered[task.task_id]["usage"]["model_calls"] == 10
    assert recovered[task.task_id]["status"] == "attempt_budget_exhausted"


@pytest.mark.docker
def test_real_visible_failure_guides_a_second_scripted_revision(data_root, docker_executor):
    from vericode.feedback import feedback_repair
    from vericode.model_io import RepairRequest
    from vericode.providers import MockProvider

    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    good = MockProvider().propose(RepairRequest(task)).candidate.replacement_source
    transport = ScriptedTransport([raw(task, wrong), raw(task, good)])
    outcome = feedback_repair(task, provider(transport), docker_executor)
    assert outcome.status == "visible_passed", f"{outcome.detail}\n{outcome.execution}"
    assert outcome.initial_execution.status == "failed"
    assert [attempt.status for attempt in outcome.history] == ["failed", "passed"]
    assert len(outcome.calls) == 2 and outcome.execution.tests_passed == 2
    observed = [outcome.initial_execution, *(attempt.execution for attempt in outcome.history)]
    assert all(result.cleanup_confirmed is True for result in observed)
    second = json.loads(transport.prompts[1].split("\n\n", 1)[1])
    assert second["current_source"] == wrong and second["visible_feedback"]["tests_failed"] == 1
    assert "E   assert" in second["visible_feedback"]["output"]
    assert "test_visible.py::test_inside" in second["visible_feedback"]["output"]
    assert "generated xml file:" not in second["visible_feedback"]["output"]
    assert "VERICODE_RESULT=" not in transport.prompts[1]
    assert load_task(data_root / "repair", "clamp").source == task.source


@pytest.mark.docker
def test_real_original_visible_pass_stops_with_zero_calls(data_root, docker_executor):
    task = load_task(data_root / "repair", "sum_positive")
    record = record_feedback_task(task, FeedbackConfiguration(backend="docker"), docker_executor)
    assert record["status"] == "visible_passed", f"{record['detail']}\n{record['repair_execution']}"
    assert record["candidate_changed"] is False and record["patch"] == ""
    assert record["usage"]["model_calls"] == record["usage"]["attempts"] == 0
    assert record["usage"]["cost_usd"] == 0 and record["attempt_history"] == []
    assert record["evaluation"] is None and record["repair_execution"]["cleanup_confirmed"] is True


@pytest.mark.docker
def test_real_feedback_batch_freezes_image_and_resume_needs_no_jobs(data_root, tmp_path, monkeypatch):
    config = FeedbackConfiguration(backend="docker")
    directory = tmp_path / "docker-feedback"
    first = batch.run_batch(data_root, data_root / "manifests/development.json", config, directory)
    assert first["pending"] == 0 and first["outcomes"] == {"visible_passed": 3}, first
    assert first["usage"]["model_calls"] == 1
    metadata = json.loads((directory / "batch.json").read_text())
    outcomes = [json.loads(line)["record"] for line in (directory / "events.jsonl").read_text().splitlines()
                if json.loads(line)["event"] == "completed"]
    assert all(record["schema_version"] == 2 and record["strategy"] == "feedback" for record in outcomes)
    for record in outcomes:
        executions = [record["initial_execution"], *(attempt["execution"] for attempt in record["attempt_history"])]
        assert all(result["image_id"] == metadata["docker_image_id"] and result["cleanup_confirmed"] is True
                   for result in executions)
    before = (directory / "events.jsonl").read_bytes()
    monkeypatch.setattr(batch, "make_executor", lambda *args: pytest.fail("completed resume needs no Docker"))
    monkeypatch.setattr(batch, "record_feedback_task", lambda *args: pytest.fail("completed resume needs no model"))
    resumed = batch.run_batch(data_root, data_root / "manifests/development.json", config, directory, resume=True)
    assert resumed["skipped_completed"] == 3 and resumed["newly_completed"] == 0
    assert (directory / "events.jsonl").read_bytes() == before
