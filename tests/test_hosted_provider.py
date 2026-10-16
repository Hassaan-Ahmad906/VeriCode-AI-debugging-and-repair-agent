from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import json
import time

import pytest

from vericode import hosted_provider as hosted
from vericode.datasets import load_task
from vericode.model_calls import TransportError
from vericode.model_io import RepairRequest
from vericode.providers import MockProvider, make_provider
from vericode.run_config import RunConfiguration
from vericode.schemas import ValidationError
from vericode.ui_service import repair_task


def connection(tmp_path, *, cap=1.0, provider="openai", timestamp=None):
    price = hosted.Price(2, 8, hosted.PRICING_URL, time.time() if timestamp is None else timestamp,
                         10000 if provider == "openrouter" else None)
    return hosted.HostedConnection(provider, "test-model", price, "secret-key", cap,
                                   hosted.SpendLedger(tmp_path / "usage.sqlite3"))


def response(content="{}", **usage):
    return {"model": "test-model", "usage": {"prompt_tokens": 100, "completion_tokens": 10, **usage},
            "choices": [{"finish_reason": "stop", "message": {"content": content}}]}


def test_verification_is_metadata_only_and_uses_standard_prices(monkeypatch):
    requests = []
    def request(host, path, **kwargs):
        requests.append((host, path, kwargs))
        return {"data": [{"id": "test-model"}]}
    monkeypatch.setattr(hosted, "request_json", request)
    monkeypatch.setattr(hosted, "request_bytes", lambda *a, **k: b"### Standard pricing data\n| test-model | $2 | $1 | - | $8 |\n### Batch pricing data\n| test-model | $1 | - | - | $4 |")
    prices = hosted.verify_connection("openai", "secret-key")
    assert prices["test-model"].input_per_million == 2
    assert prices["test-model"].output_per_million == 8
    assert len(requests) == 1 and requests[0][1] == "/v1/models"
    assert "payload" not in requests[0][2]
    with pytest.raises(TransportError):
        hosted.parse_openai_prices("unexpected page")


def test_durable_ledger_reserves_before_call_and_holds_unknown_outcome(tmp_path):
    conn = connection(tmp_path)
    identity = conn.ledger.reserve(conn.scope, 0.5)
    with pytest.raises(TransportError, match="unresolved"):
        conn.ledger.reserve(conn.scope, 0.01)
    conn.ledger.settle(identity, 0.25)
    again = connection(tmp_path)
    assert again.ledger.status(conn.scope)["accounted_usd"] == 0.25
    with pytest.raises(TransportError, match="limit reached"):
        again.ledger.reserve(conn.scope, 0.76)
    identity = again.ledger.reserve(conn.scope, 0.5)
    again.ledger.settle(identity)
    assert connection(tmp_path).ledger.status(conn.scope)["blocked"]
    with pytest.raises(ValidationError):
        connection(tmp_path, cap=0.1)
    assert "secret-key" not in conn.ledger.path.read_bytes().decode("latin-1")


def test_concurrent_calls_cannot_both_reserve_same_credential(tmp_path):
    conn = connection(tmp_path)
    def reserve(_):
        try:
            return conn.ledger.reserve(conn.scope, 0.1)
        except TransportError:
            return None
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(reserve, [1, 2]))
    assert sum(value is not None for value in results) == 1


@pytest.mark.parametrize("failure", ["budget", "expired"])
def test_no_network_call_before_budget_and_fresh_pricing(monkeypatch, tmp_path, failure):
    conn = connection(tmp_path, cap=0.000001 if failure == "budget" else 1,
                      timestamp=0 if failure == "expired" else None)
    def forbidden(*a, **k):
        pytest.fail("HTTP must not be sent")
    monkeypatch.setattr(hosted, "request_json", forbidden)
    with pytest.raises(TransportError):
        hosted.HostedTransport(conn).complete("json", model=conn.model, max_output_tokens=512, timeout_seconds=1)


def test_failed_call_keeps_reservation_and_never_logs_secret(monkeypatch, tmp_path):
    conn = connection(tmp_path)
    def fail(*a, **k):
        raise RuntimeError("secret-key in unsafe provider error")
    monkeypatch.setattr(hosted, "request_json", fail)
    with pytest.raises(TransportError) as error:
        hosted.HostedTransport(conn).complete("json", model=conn.model, max_output_tokens=512, timeout_seconds=1)
    assert "secret-key" not in str(error.value)
    assert error.value.usage.cost_usd is None
    assert conn.ledger.status(conn.scope)["blocked"]


def test_hosted_repair_uses_shared_controller_and_exports_no_credentials(monkeypatch, tmp_path, data_root):
    task = load_task(data_root / "repair", "clamp")
    candidate = MockProvider().propose(RepairRequest(task)).candidate
    requests = []
    def request(host, path, **kwargs):
        requests.append(kwargs)
        return response(json.dumps(asdict(candidate)))
    monkeypatch.setattr(hosted, "request_json", request)
    conn = connection(tmp_path)
    config = RunConfiguration(provider="openai", model=conn.model)
    with pytest.raises(ValidationError, match="Connect"):
        make_provider(config)
    record = repair_task(task, config, conn)
    assert record["paid_api_enabled"] is True
    assert record["evaluation"] is None
    assert record["run_kind"] == "hosted_model_run"
    assert record["usage"]["input_tokens"] == 100
    assert record["usage"]["cost_usd"] == pytest.approx(0.00028)
    assert "secret-key" not in json.dumps(record)
    assert conn.ledger.status(conn.scope)["accounted_usd"] == pytest.approx(0.00028)
    assert requests[0]["payload"]["store"] is False
    assert requests[0]["payload"]["max_completion_tokens"] == config.generation.output_tokens
    with pytest.raises(ValidationError, match="Connect"):
        make_provider(config)  # Context must reset after a run.


def test_openrouter_uses_provider_reported_cost_and_route_price_cap(monkeypatch, tmp_path):
    conn = connection(tmp_path, provider="openrouter")
    requests = []
    def request(*a, **kwargs):
        requests.append(kwargs["payload"])
        return response(cost=0.0002)
    monkeypatch.setattr(hosted, "request_json", request)
    result = hosted.HostedTransport(conn).complete("json", model=conn.model, max_output_tokens=128, timeout_seconds=1)
    assert result.usage.cost_usd == 0.0002
    assert requests[0]["provider"]["max_price"] == {"prompt": 2, "completion": 8}
    assert requests[0]["provider"]["allow_fallbacks"] is False


def test_connections_are_isolated_across_threads(tmp_path):
    conn = connection(tmp_path)
    with hosted.use_connection(conn):
        assert hosted.connection_metadata()
        with ThreadPoolExecutor(1) as pool:
            assert pool.submit(hosted.connection_metadata).result() == {}
    assert hosted.connection_metadata() == {}


@pytest.mark.parametrize("strategy", ["feedback", "augmented"])
def test_hosted_feedback_and_generation_share_budget_and_keep_evaluator_separate(monkeypatch, tmp_path, data_root, strategy):
    from vericode.augmented import record_augmented_task
    from vericode.feedback_run import record_feedback_task
    from vericode.run_config import FeedbackConfiguration, AugmentedConfiguration
    from test_feedback import FAILED, PASSED, ScriptedExecutor
    task = load_task(data_root / "repair", "clamp")
    candidate = MockProvider().propose(RepairRequest(task)).candidate
    answers = ([response('{"cases":[{"args":[1,0,5],"expected":1}]}')] if strategy == "augmented" else []) + [response(json.dumps(asdict(candidate)))]
    monkeypatch.setattr(hosted, "request_json", lambda *a, **k: answers.pop(0))
    conn = connection(tmp_path)
    cls = AugmentedConfiguration if strategy == "augmented" else FeedbackConfiguration
    config = cls(provider="openai", model=conn.model)
    controller = record_augmented_task if strategy == "augmented" else record_feedback_task
    with hosted.use_connection(conn):
        record = controller(task, config, ScriptedExecutor([FAILED, PASSED]))
    count = 2 if strategy == "augmented" else 1
    assert record["status"] == "visible_passed" and record["evaluation"] is None
    assert record["usage"]["model_calls"] == count
    assert conn.ledger.status(conn.scope)["calls"] == count
    assert record["usage"]["cost_usd"] == pytest.approx(count * 0.00028)
    assert not answers


@pytest.mark.parametrize("status,size", [(302, 0), (401, 0), (200, 5)])
def test_http_rejects_redirect_error_and_oversized_body_without_exposing_key(monkeypatch, status, size):
    sent = []
    class Response:
        def __init__(self):
            self.status = status
        def read(self, limit):
            return b"x" * size
    class Connection:
        def __init__(self, *a, **k):
            pass
        def request(self, *a):
            sent.append(a)
        def getresponse(self):
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(hosted.http.client, "HTTPSConnection", Connection)
    with pytest.raises(TransportError) as error:
        hosted.request_bytes("api.openai.com", "/v1/models", key="secret-key", limit=4)
    assert len(sent) == 1 and "secret-key" not in str(error.value)
    assert sent[0][3]["Authorization"] == "Bearer secret-key"
