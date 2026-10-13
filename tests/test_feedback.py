from dataclasses import asdict, replace
import json

import pytest

from vericode.datasets import load_task
from vericode.feedback import FeedbackLimits, VisibleFeedback, feedback_repair
from vericode.jobs import MockJobExecutor
from vericode.model_calls import RawCompletion, StructuredProvider, TransientTransportError
from vericode.model_io import GenerationLimits, RepairRequest, Usage, summarize_calls
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


def test_repeated_patch_stops_without_reexecuting_and_retains_last_tested_candidate(data_root):
    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    transport = ScriptedTransport([raw(task, wrong), raw(task, wrong)])
    executor = ScriptedExecutor([FAILED, FAILED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "repeated_patch" and outcome.agent_accepted is False
    assert len(executor.jobs) == 2 and len(outcome.calls) == 2
    assert outcome.candidate.replacement_source == wrong
    assert outcome.history[-1].execution is None


def test_distinct_failed_patches_exhaust_attempts(data_root):
    task = load_task(data_root / "repair", "clamp")
    transport = ScriptedTransport([raw(task, f"def clamp(value, lower, upper):\n    return {number}\n") for number in (0, 1)])
    executor = ScriptedExecutor([FAILED, FAILED, FAILED])
    outcome = feedback_repair(task, provider(transport), executor, FeedbackLimits(max_attempts=2))
    assert outcome.status == "attempt_budget_exhausted" and outcome.agent_accepted is False
    assert len(outcome.history) == 2 and len(outcome.calls) == 2 and len(executor.jobs) == 3


def test_original_visible_success_uses_zero_model_calls(data_root):
    task = load_task(data_root / "repair", "sum_positive")
    transport = ScriptedTransport([])
    executor = ScriptedExecutor([PASSED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "visible_passed" and outcome.agent_accepted is True
    assert outcome.candidate.replacement_source == task.source and outcome.patch == ""
    assert not outcome.calls and not outcome.history and not transport.prompts
    assert len(executor.jobs) == 1


@pytest.mark.parametrize("results", [
    [ExecutionResult("sandbox", "infrastructure_error", cleanup_confirmed=True)],
    [FAILED, ExecutionResult("sandbox", "infrastructure_error", cleanup_confirmed=False)],
])
def test_infrastructure_failure_stops_without_another_request(data_root, results):
    task = load_task(data_root / "repair", "clamp")
    transport = ScriptedTransport([raw(task, "def clamp(value, lower, upper):\n    return lower\n")])
    executor = ScriptedExecutor(results)
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "infrastructure_error" and outcome.agent_accepted is None
    assert len(transport.prompts) == len(results) - 1
    assert len(executor.jobs) == len(results)


@pytest.mark.parametrize("text", ["{bad", "```json\n{}\n```", json.dumps({
    "task_id": "clamp", "target_file": "../evaluation/suite.json", "replacement_source": "def clamp(): pass"}),
    '{"task_id":"clamp","task_id":"other","target_file":"solution.py","replacement_source":"def clamp(): pass"}',
])
def test_malformed_response_stops_without_execution_or_a_second_answer(data_root, text):
    task = load_task(data_root / "repair", "clamp")
    transport = ScriptedTransport([RawCompletion(text, Usage(7, 4, 0.0))])
    executor = ScriptedExecutor([FAILED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "invalid_response" and outcome.agent_accepted is False
    assert len(transport.prompts) == len(executor.jobs) == len(outcome.calls) == 1
    assert outcome.candidate is None and outcome.history[0].execution is None
    assert summarize_calls(outcome.calls)["input_tokens"] == 7


@pytest.mark.parametrize("source,task_id", [
    ("def clamp(:\n    return 0\n", "clamp"),
    ("def other():\n    return 0\n", "clamp"),
    ("def clamp(value, lower, upper):\n    return lower\n", "count_vowels"),
])
def test_invalid_patch_retains_rejection_without_running_it(data_root, source, task_id):
    task = load_task(data_root / "repair", "clamp")
    response = RawCompletion(json.dumps(asdict(Candidate(task_id, "solution.py", source))), Usage(10, 4, 0.0))
    transport = ScriptedTransport([response])
    executor = ScriptedExecutor([FAILED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "invalid_patch" and outcome.agent_accepted is False
    assert len(transport.prompts) == len(executor.jobs) == 1
    assert outcome.candidate is None and outcome.patch is None
    assert outcome.history[0].candidate.replacement_source == source
    assert outcome.history[0].execution is None


def test_rejection_on_revision_preserves_previously_checked_patch_and_all_usage(data_root):
    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    transport = ScriptedTransport([raw(task, wrong), RawCompletion("{bad", Usage(8, 3, 0.0))])
    executor = ScriptedExecutor([FAILED, FAILED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "invalid_response" and outcome.candidate.replacement_source == wrong
    assert outcome.execution == FAILED and len(executor.jobs) == 2
    assert [attempt.call_indices for attempt in outcome.history] == [(1,), (2,)]
    assert summarize_calls(outcome.calls)["input_tokens"] == 20


@pytest.mark.parametrize("status", ["test_error", "timeout", "output_limit", "resource_limit"])
def test_candidate_errors_can_supply_visible_feedback_for_a_bounded_revision(data_root, status):
    task = load_task(data_root / "repair", "clamp")
    good = MockProvider().propose(RepairRequest(task)).candidate.replacement_source
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    transport = ScriptedTransport([raw(task, wrong), raw(task, good)])
    problem = ExecutionResult("sandbox", status, output="visible candidate error", cleanup_confirmed=True)
    executor = ScriptedExecutor([FAILED, problem, PASSED])
    outcome = feedback_repair(task, provider(transport), executor)
    second = json.loads(transport.prompts[1].split("\n\n", 1)[1])
    assert second["visible_feedback"]["status"] == status
    assert outcome.status == "visible_passed" and len(outcome.calls) == 2


def test_returning_to_an_earlier_source_stops_a_cycle(data_root):
    task = load_task(data_root / "repair", "clamp")
    sources = [f"def clamp(value, lower, upper):\n    return {number}\n" for number in (0, 1, 0)]
    transport = ScriptedTransport([raw(task, source) for source in sources])
    executor = ScriptedExecutor([FAILED, FAILED, FAILED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "repeated_patch" and len(executor.jobs) == 3
    assert outcome.candidate.replacement_source == sources[1]
    assert outcome.history[-1].candidate.replacement_source == sources[0]
    assert len(outcome.calls) == 3 and outcome.history[-1].execution is None


def test_proposing_original_source_stops_before_another_job(data_root):
    task = load_task(data_root / "repair", "clamp")
    transport = ScriptedTransport([raw(task, task.source)])
    executor = ScriptedExecutor([FAILED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "repeated_patch" and len(executor.jobs) == 1
    assert len(outcome.calls) == 1 and outcome.candidate is None


def test_last_request_retry_is_clipped_to_remaining_global_budget(data_root):
    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    transport = ScriptedTransport([TransientTransportError("unknown usage"), raw(task, wrong),
                                   TransientTransportError("last call")])
    executor = ScriptedExecutor([FAILED, FAILED])
    outcome = feedback_repair(task, provider(transport), executor, FeedbackLimits(max_model_calls=3))
    assert outcome.status == "transient_error"
    assert len(outcome.calls) == len(transport.prompts) == 3 and len(outcome.history) == 2
    assert transport.prompts[0] == transport.prompts[1] != transport.prompts[2]
    assert [attempt.call_indices for attempt in outcome.history] == [(1, 2), (3,)]
    assert [call.call_index for call in outcome.calls] == [1, 2, 3]
    assert summarize_calls(outcome.calls)["cost_usd"] is None


def test_oversized_prompt_stops_before_transport(data_root):
    task = load_task(data_root / "repair", "clamp")
    transport = ScriptedTransport([])
    limited = StructuredProvider(transport, provider="test_mock", model="scripted", limits=GenerationLimits(prompt_bytes=1024))
    outcome = feedback_repair(replace(task, specification="x" * 3000), limited, ScriptedExecutor([FAILED]))
    assert outcome.status == "input_limit" and not outcome.calls and not transport.prompts
    assert len(outcome.history) == 1 and outcome.history[0].call_indices == ()


@pytest.mark.parametrize("phase", ["initial", "candidate"])
def test_unexpected_executor_exception_is_sanitized_and_stops(data_root, phase):
    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    transport = ScriptedTransport([raw(task, wrong)])
    error = RuntimeError("credential-SENTINEL should never be logged")
    results = [error] if phase == "initial" else [FAILED, error]
    outcome = feedback_repair(task, provider(transport), ScriptedExecutor(results))
    assert outcome.status == "infrastructure_error" and outcome.agent_accepted is None
    assert "credential-SENTINEL" not in json.dumps(asdict(outcome))
    assert len(transport.prompts) == (0 if phase == "initial" else 1)


@pytest.mark.parametrize("phase", ["initial", "candidate"])
def test_unconfirmed_cleanup_overrides_an_apparent_pass(data_root, phase):
    task = load_task(data_root / "repair", "clamp")
    transport = ScriptedTransport([raw(task, "def clamp(value, lower, upper):\n    return lower\n")])
    uncertain = replace(PASSED, cleanup_confirmed=False)
    results = [uncertain] if phase == "initial" else [FAILED, uncertain]
    outcome = feedback_repair(task, provider(transport), ScriptedExecutor(results))
    assert outcome.status == "infrastructure_error" and outcome.agent_accepted is None
    assert len(transport.prompts) == (0 if phase == "initial" else 1)


def test_paid_provider_is_blocked_before_visible_execution(data_root):
    task = load_task(data_root / "repair", "clamp")
    transport = ScriptedTransport([])
    transport.offline = False
    executor = ScriptedExecutor([])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "paid_execution_disabled"
    assert not transport.prompts and not executor.jobs and not outcome.calls


def test_feedback_boundary_excludes_controller_and_evaluator_information(data_root):
    task = load_task(data_root / "repair", "clamp")
    observed = replace(FAILED, output="visible assertion\n-- generated xml file: /workspace/report-SENTINEL.xml --\nVERICODE_RESULT=private-protocol-SENTINEL\n",
                       detail="/private/evaluator-SENTINEL/suite.json", job_name="controller-job-SENTINEL",
                       image_id="controller-image-SENTINEL")
    sources = ["def clamp(value, lower, upper):\n    return lower\n",
               MockProvider().propose(RepairRequest(task)).candidate.replacement_source]
    transport = ScriptedTransport([raw(task, source) for source in sources])
    executor = ScriptedExecutor([observed, observed, PASSED])
    outcome = feedback_repair(task, provider(transport), executor)
    assert outcome.status == "visible_passed"
    for prompt in transport.prompts:
        assert "SENTINEL" not in prompt
        payload = json.loads(prompt.split("\n\n", 1)[1])
        assert set(payload) == {"task", "current_source", "visible_feedback", "attempt"}
        assert payload["task"] == asdict(task)
        assert set(payload["visible_feedback"]) == {
            "mode", "status", "tests_passed", "tests_failed", "tests_errors", "tests_skipped", "output", "output_truncated"}
        assert payload["visible_feedback"]["output"] == "visible assertion"
    assert all(tests == task.repair_tests for _, tests in executor.jobs)


def test_feedback_output_cap_preserves_valid_utf8_and_reports_truncation():
    feedback = VisibleFeedback.from_execution(replace(FAILED, output="\u2603" * 1000), 256)
    assert len(feedback.output.encode("utf-8")) == 255 and feedback.output_truncated is True
    assert "\ufffd" not in feedback.output


def test_success_on_last_allowed_call_wins_over_budget_exhaustion(data_root):
    task = load_task(data_root / "repair", "clamp")
    good = MockProvider().propose(RepairRequest(task)).candidate.replacement_source
    outcome = feedback_repair(task, provider(ScriptedTransport([raw(task, good)])),
                              ScriptedExecutor([FAILED, PASSED]), FeedbackLimits(max_attempts=1, max_model_calls=1))
    assert outcome.status == "visible_passed" and outcome.agent_accepted is True
    assert len(outcome.calls) == len(outcome.history) == 1


def test_timeout_at_attempt_limit_does_not_invent_rejected_test_counts(data_root):
    task = load_task(data_root / "repair", "clamp")
    wrong = "def clamp(value, lower, upper):\n    return lower\n"
    timeout = ExecutionResult("sandbox", "timeout", cleanup_confirmed=True)
    outcome = feedback_repair(task, provider(ScriptedTransport([raw(task, wrong)])),
                              ScriptedExecutor([FAILED, timeout]), FeedbackLimits(max_attempts=1))
    assert outcome.status == "attempt_budget_exhausted" and outcome.agent_accepted is None
    assert outcome.execution.status == "timeout" and outcome.execution.tests_failed is None
