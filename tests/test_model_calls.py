from dataclasses import asdict, replace
import json

import pytest

from vericode.datasets import load_task
from vericode.model_calls import ProviderFailure, RawCompletion, StructuredProvider, TransientTransportError
from vericode.model_io import GenerationLimits, RepairRequest, Usage, summarize_calls
from vericode.providers import MockProvider
from vericode.schemas import ValidationError


class ScriptedTransport:
    offline = True

    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def complete(self, prompt, **options):
        self.requests.append((prompt, options))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def raw_candidate(data_root, usage=Usage(cost_usd=0.0)):
    task = load_task(data_root / "repair", "clamp")
    candidate = MockProvider().propose(RepairRequest(task)).candidate
    return RawCompletion(json.dumps(asdict(candidate)), usage, "actual-mock-revision")


def provider(transport, **limits):
    return StructuredProvider(transport, provider="test_mock", model="configured-model", limits=GenerationLimits(**limits))


def test_transient_retry_counts_usage_and_preserves_identical_prompt(data_root):
    transport = ScriptedTransport([
        TransientTransportError("safe simulated failure", usage=Usage(10, 2, 0.01)),
        raw_candidate(data_root, Usage(20, 5, 0.02)),
    ])
    response = provider(transport).propose(RepairRequest(load_task(data_root / "repair", "clamp")))
    summary = summarize_calls(response.calls)
    assert len(transport.requests) == 2
    assert transport.requests[0] == transport.requests[1]
    assert transport.requests[0][1] == {"model": "configured-model", "max_output_tokens": 2048, "timeout_seconds": 15.0}
    assert summary["model_calls"] == 2
    assert summary["input_tokens"] == 30 and summary["output_tokens"] == 7
    assert summary["cost_usd"] == pytest.approx(0.03)
    assert response.model == "actual-mock-revision"
    assert [call.status for call in response.calls] == ["transient_error", "completed"]


def test_retry_budget_exhaustion_does_not_invent_zero_cost(data_root):
    transport = ScriptedTransport([TransientTransportError("failed") for _ in range(4)])
    with pytest.raises(ProviderFailure) as error:
        provider(transport).propose(RepairRequest(load_task(data_root / "repair", "clamp")))
    assert len(transport.requests) == 3
    assert len(error.value.calls) == 3
    assert error.value.code == "transient_error"
    summary = summarize_calls(error.value.calls)
    assert summary["cost_usd"] is None and summary["input_tokens"] is None
    assert summary["known_cost_usd"] == 0
    assert summary["usage_complete"] is False


def test_partial_usage_keeps_known_totals_and_unknown_grand_total(data_root):
    transport = ScriptedTransport([TransientTransportError("unknown billing"), raw_candidate(data_root, Usage(9, 3, 0.02))])
    response = provider(transport).propose(RepairRequest(load_task(data_root / "repair", "clamp")))
    summary = summarize_calls(response.calls)
    assert summary["cost_usd"] is None and summary["known_cost_usd"] == 0.02
    assert summary["input_tokens"] is None and summary["known_input_tokens"] == 9


@pytest.mark.parametrize("text", [
    "```json\n{}\n```", '[]', '{}', '{bad',
    '{"task_id":"clamp","task_id":"other","target_file":"solution.py","replacement_source":"def clamp(): pass"}',
    '{"task_id":"clamp","target_file":"../test_eval.py","replacement_source":"def clamp(): pass"}',
    '{"task_id":"clamp","target_file":"solution.py","replacement_source":null}',
    '{"task_id":"clamp","target_file":"solution.py","replacement_source":"def clamp(): pass","extra":NaN}',
], ids=["fenced-json", "array", "missing-fields", "syntax", "duplicate-key", "forbidden-target", "null-source", "nonfinite"])
def test_malformed_response_is_rejected_without_a_second_answer(data_root, text):
    transport = ScriptedTransport([RawCompletion(text, Usage(10, 4, 0.01)), raw_candidate(data_root)])
    with pytest.raises(ProviderFailure) as error:
        provider(transport).propose(RepairRequest(load_task(data_root / "repair", "clamp")))
    assert error.value.code == "invalid_response"
    assert len(transport.requests) == 1
    assert summarize_calls(error.value.calls)["cost_usd"] == 0.01


def test_large_prompt_is_rejected_before_transport(data_root):
    task = replace(load_task(data_root / "repair", "clamp"), specification="x" * 3000)
    transport = ScriptedTransport([])
    with pytest.raises(ProviderFailure) as error:
        provider(transport, prompt_bytes=1024).propose(RepairRequest(task))
    assert error.value.code == "input_limit"
    assert error.value.calls == () and transport.requests == []


def test_response_bytes_and_reported_token_overrun_are_rejected(data_root):
    task = RepairRequest(load_task(data_root / "repair", "clamp"))
    for raw, limits in (
        (RawCompletion("x" * 2000), {"response_bytes": 1024}),
        (raw_candidate(data_root, Usage(output_tokens=2049)), {}),
    ):
        transport = ScriptedTransport([raw])
        with pytest.raises(ProviderFailure) as error:
            provider(transport, **limits).propose(task)
        assert error.value.code == "invalid_response" and len(transport.requests) == 1


def test_nonoffline_transport_is_blocked_even_with_environment_budget(data_root, monkeypatch):
    transport = ScriptedTransport([raw_candidate(data_root)])
    transport.offline = False
    monkeypatch.setenv("VERICODE_SPENDING_CAP_USD", "100")
    with pytest.raises(ProviderFailure) as error:
        provider(transport).propose(RepairRequest(load_task(data_root / "repair", "clamp")))
    assert error.value.code == "paid_execution_disabled"
    assert transport.requests == []


def test_exception_details_do_not_leak_credentials(data_root):
    transport = ScriptedTransport([RuntimeError("credential-sentinel must not be logged")])
    with pytest.raises(ProviderFailure) as error:
        provider(transport).propose(RepairRequest(load_task(data_root / "repair", "clamp")))
    assert "credential-sentinel" not in str(error.value)
    assert "credential-sentinel" not in json.dumps([asdict(call) for call in error.value.calls])


@pytest.mark.parametrize("usage", [
    {"input_tokens": True}, {"output_tokens": -1}, {"cost_usd": float("nan")}, {"cost_usd": -0.1},
])
def test_invalid_usage_cannot_be_logged_as_valid(usage):
    with pytest.raises(ValidationError):
        Usage(**usage)
