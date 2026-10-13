from dataclasses import asdict
import json

from vericode.datasets import load_task
from vericode.feedback import FeedbackLimits, feedback_repair
from vericode.jobs import MockJobExecutor
from vericode.model_calls import RawCompletion, StructuredProvider, TransientTransportError
from vericode.model_io import RepairRequest, Usage, summarize_calls
from vericode.providers import MockProvider
from vericode.results import ExecutionResult
from vericode.schemas import Candidate


FAILED = ExecutionResult("sandbox", "failed", tests_passed=1, tests_failed=1,
                         output="test_visible.py: AssertionError: expected 5, got 1",
                         cleanup_confirmed=True)
PASSED = ExecutionResult("sandbox", "passed", tests_passed=2, tests_failed=0, cleanup_confirmed=True)


class ScriptedTransport:
    offline = True

    def __init__(self, responses, events=None):
        self.responses = iter(responses)
        self.prompts = []
        self.events = events if events is not None else []

    def complete(self, prompt, **options):
        self.prompts.append(prompt)
        self.events.append("model")
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


class ScriptedExecutor:
    """Pre-recorded observations only; never evaluates source on the host."""

    def __init__(self, results, events=None):
        self.results = iter(results)
        self.jobs = []
        self.events = events if events is not None else []

    def run(self, source, tests):
        self.jobs.append((source, tests))
        self.events.append("execute")
        result = next(self.results)
        if isinstance(result, Exception):
            raise result
        return result


def raw(task, source):
    return RawCompletion(json.dumps(asdict(Candidate(task.task_id, "solution.py", source))), Usage(12, 6, 0.0))


def provider(transport):
    return StructuredProvider(transport, provider="test_mock", model="scripted")


def test_revision_uses_latest_candidate_and_visible_feedback(data_root):
    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    good = MockProvider().propose(RepairRequest(task)).candidate.replacement_source
    events = []
    transport = ScriptedTransport([raw(task, wrong), raw(task, good)], events)
    executor = ScriptedExecutor([FAILED, FAILED, PASSED], events)
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "visible_passed" and outcome.agent_accepted is True
    assert events == ["execute", "model", "execute", "model", "execute"]
    first, second = [json.loads(prompt.split("\n\n", 1)[1]) for prompt in transport.prompts]
    assert first["current_source"] == task.source
    assert second["current_source"] == wrong and second["attempt"] == 2
    assert second["visible_feedback"]["tests_failed"] == 1
    assert "expected 5" in second["visible_feedback"]["output"]
    assert outcome.candidate.replacement_source == good
    assert [call.call_index for call in outcome.calls] == [1, 2]
    assert summarize_calls(outcome.calls)["input_tokens"] == 24
    assert len(outcome.history) == 2
    assert all(tests == task.repair_tests for _, tests in executor.jobs)


def test_transport_retry_consumes_shared_model_call_budget(data_root):
    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    transport = ScriptedTransport([TransientTransportError("unknown usage"), raw(task, wrong)])
    executor = ScriptedExecutor([FAILED, FAILED])
    outcome = feedback_repair(task, provider(transport), executor, FeedbackLimits(max_model_calls=2))
    assert outcome.status == "model_call_budget_exhausted"
    assert len(outcome.history) == 1 and len(transport.prompts) == 2
    assert transport.prompts[0] == transport.prompts[1]
    assert len(executor.jobs) == 2
    assert summarize_calls(outcome.calls)["cost_usd"] is None


def test_mock_has_no_measured_feedback_or_acceptance(data_root):
    task = load_task(data_root / "repair", "clamp")
    outcome = feedback_repair(task, MockProvider(), MockJobExecutor())
    assert outcome.status == "candidate_ready" and outcome.agent_accepted is None
    assert outcome.initial_execution.status == "not_executed"
    assert outcome.execution.status == "not_executed"
    assert len(outcome.calls) == 1 and len(outcome.history) == 1
