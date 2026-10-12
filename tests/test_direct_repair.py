from dataclasses import asdict
import json
import shutil

import pytest

from vericode.cli import main
from vericode.datasets import load_task
from vericode.direct_run import record_direct_task, run_direct
from vericode.jobs import MockJobExecutor
from vericode.model_calls import RawCompletion, StructuredProvider
from vericode.model_io import RepairRequest, Usage, summarize_calls
from vericode.providers import MockProvider
from vericode.results import ExecutionResult
from vericode.run_config import RunConfiguration
from vericode.strategies import direct_repair
from vericode.schemas import Candidate, ValidationError


class RecordingTransport:
    offline = True

    def __init__(self, responses, events=None):
        self.responses = iter(responses)
        self.prompts = []
        self.events = events if events is not None else []

    def complete(self, prompt, **kwargs):
        self.prompts.append(prompt)
        self.events.append("model")
        return next(self.responses)


class RecordingExecutor:
    def __init__(self, result=None, events=None):
        self.result = result or ExecutionResult("mock", "not_executed")
        self.jobs = []
        self.events = events if events is not None else []

    def run(self, source, tests):
        self.events.append("execute")
        self.jobs.append((source, tests))
        return self.result


def raw(task, source=None, task_id=None):
    candidate = Candidate(task_id or task.task_id, "solution.py", source or task.source)
    return RawCompletion(json.dumps(asdict(candidate)), Usage(cost_usd=0.0), "scripted-test")


def model(transport):
    return StructuredProvider(transport, provider="test_mock", model="scripted-test")


def test_one_response_precedes_execution_and_does_not_receive_feedback(data_root):
    task = load_task(data_root / "repair", "clamp")
    events = []
    transport = RecordingTransport([raw(task)], events)
    executor = RecordingExecutor(ExecutionResult("sandbox", "failed", tests_passed=1, tests_failed=1), events)
    outcome = direct_repair(task, model(transport), executor)
    assert events == ["model", "execute"]
    assert len(transport.prompts) == 1
    assert executor.jobs == [(task.source, task.repair_tests)]
    assert "test_outside_bounds" not in transport.prompts[0]
    assert outcome.status == "visible_failed" and outcome.agent_accepted is False
    assert outcome.patch == ""  # An unchanged proposal is recorded, not rerolled.


@pytest.mark.parametrize("source,task_id,message", [
    ("def clamp(:", "clamp", "parseable"),
    ("def different(): return 0", "clamp", "top-level function"),
    ("def clamp(): return 0", "other", "task_id"),
])
def test_invalid_patch_never_executes_or_revises(data_root, source, task_id, message):
    task = load_task(data_root / "repair", "clamp")
    transport = RecordingTransport([raw(task, source, task_id), raw(task)])
    executor = RecordingExecutor()
    outcome = direct_repair(task, model(transport), executor)
    assert outcome.status == "invalid_patch" and message in outcome.detail
    assert outcome.agent_accepted is False and outcome.execution is None
    assert len(transport.prompts) == 1 and executor.jobs == []
    assert summarize_calls(outcome.calls)["model_calls"] == 1


def test_malformed_response_remains_separate_from_invalid_patch(data_root):
    task = load_task(data_root / "repair", "clamp")
    transport = RecordingTransport([RawCompletion("bad JSON", Usage(10, 2, 0.01)), raw(task)])
    executor = RecordingExecutor()
    outcome = direct_repair(task, model(transport), executor)
    assert outcome.status == "invalid_response"
    assert outcome.candidate is None and executor.jobs == []
    assert len(transport.prompts) == 1
    assert summarize_calls(outcome.calls)["cost_usd"] == 0.01


def test_execution_failure_retains_candidate_and_sanitizes_exception(data_root):
    task = load_task(data_root / "repair", "clamp")

    class BrokenExecutor:
        def run(self, *args):
            raise RuntimeError("credential-sentinel")

    outcome = direct_repair(task, MockProvider(), BrokenExecutor())
    assert outcome.status == "infrastructure_error"
    assert outcome.candidate is not None and outcome.patch
    assert outcome.agent_accepted is None
    assert "credential-sentinel" not in outcome.detail
    assert len(outcome.calls) == 1


def test_strategy_itself_blocks_paid_provider_before_any_call(data_root):
    class PaidProvider:
        offline = False

        def propose(self, request):
            pytest.fail("paid provider must not be invoked")

    outcome = direct_repair(load_task(data_root / "repair", "clamp"), PaidProvider(), RecordingExecutor())
    assert outcome.status == "paid_execution_disabled"
    assert outcome.calls == ()


def test_direct_record_loads_no_evaluator_inputs(data_root, tmp_path):
    shutil.copytree(data_root / "repair", tmp_path / "repair")
    shutil.copytree(data_root / "manifests", tmp_path / "manifests")
    record = run_direct(tmp_path, "clamp", RunConfiguration())
    assert record["strategy"] == "direct" and record["run_kind"] == "mock"
    assert record["status"] == "candidate_ready" and record["agent_accepted"] is None
    assert record["evaluation"] is None
    assert record["usage"]["attempts"] == record["usage"]["repair_responses"] == 1
    assert record["usage"]["model_calls"] == 1
    assert record["usage"]["input_tokens"] is None and record["usage"]["cost_usd"] == 0
    assert len(record["model_calls"]) == len(record["attempt_history"]) == 1
    assert str(tmp_path) not in record["prompt"]


def test_cli_direct_repair_saves_offline_record(data_root, tmp_path, capsys):
    output = tmp_path / "repair.json"
    assert main(["repair", "--data-root", str(data_root), "--model", "mock-label", "--output", str(output)]) == 0
    record = json.loads(capsys.readouterr().out)
    assert json.loads(output.read_text(encoding="utf-8")) == record
    assert record["configuration"]["model"] == "mock-label"
    assert record["model_calls"][0]["configured_model"] == "mock-label"


def test_configuration_roundtrip_and_invalid_provider():
    config = RunConfiguration()
    assert RunConfiguration.from_dict(config.to_dict()) == config
    data = config.to_dict()
    data["provider"] = "paid-provider"
    with pytest.raises(ValidationError, match="only mock"):
        RunConfiguration.from_dict(data)


@pytest.mark.docker
def test_direct_mock_response_then_real_visible_suite(data_root, docker_executor):
    task = load_task(data_root / "repair", "clamp")
    original = task.source
    record = record_direct_task(task, RunConfiguration(backend="docker"), docker_executor)
    assert record["status"] == "visible_passed", f"{record['detail']}\n{record['repair_execution']}"
    assert record["agent_accepted"] is True
    assert record["repair_execution"]["tests_passed"] == 2
    assert record["repair_execution"]["cleanup_confirmed"] is True
    assert record["run_kind"] == "sandbox_smoke"
    assert record["evaluation"] is None and record["usage"]["model_calls"] == 1
    assert load_task(data_root / "repair", "clamp").source == original
