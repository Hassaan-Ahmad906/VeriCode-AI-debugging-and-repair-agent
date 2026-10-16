from dataclasses import replace
import json

import pytest

from vericode import local_provider
from vericode.augmented import record_augmented_task
from vericode.datasets import load_task
from vericode.direct_run import record_direct_task
from vericode.model_calls import ProviderFailure, TransportError
from vericode.model_io import RepairRequest
from vericode.run_config import AugmentedConfiguration, RunConfiguration
from vericode.schemas import ValidationError


@pytest.mark.parametrize("tag", ["gpt-cloud", "foo/bar", "http://example.com/model", "x@external"])
def test_cloud_model_tags_rejected_before_network(tag):
    with pytest.raises(ValidationError):
        RunConfiguration(provider="ollama", model=tag)


def test_local_repair_uses_only_visible_input_and_records_real_usage(monkeypatch, data_root):
    task = load_task(data_root / "repair", "clamp")
    requests = []
    def local(path, body, timeout):
        requests.append((path, body))
        if path == "/api/show":
            return {"model_info": {"general.architecture": "qwen2"}}
        return {"done": True, "model": "my-local-model", "prompt_eval_count": 50, "eval_count": 30,
                "message": {"content": json.dumps({"task_id": task.task_id, "target_file": "solution.py",
                "replacement_source": "def clamp(value, lower, upper):\n    return max(lower, min(value, upper))\n"})}}
    monkeypatch.setattr(local_provider, "local_request", local)
    record = record_direct_task(task, RunConfiguration(provider="ollama", model="my-local-model"))
    assert record["run_kind"] == "local_model_smoke"
    assert record["usage"]["input_tokens"] == 50
    assert record["usage"]["cost_usd"] == 0
    assert record["evaluation"] is None
    assert requests[1][1]["messages"] == [{"role": "user", "content": RepairRequest(task).prompt()}]
    assert "evaluation" not in requests[1][1]["messages"][0]["content"]
    schema = requests[1][1]["format"]
    assert schema["required"] == ["task_id", "target_file", "replacement_source"]
    assert schema["properties"]["task_id"]["const"] == task.task_id
    assert schema["additionalProperties"] is False


def test_local_alias_to_cloud_is_blocked(monkeypatch):
    monkeypatch.setattr(local_provider, "local_request", lambda *args: {"remote_host": "https://cloud.example", "model_info": {"x": 1}})
    with pytest.raises(TransportError):
        local_provider.require_local_model("innocent-name", 1)


def test_redirect_or_oversized_http_response_never_followed(monkeypatch):
    class Connection:
        status = 302
        def __init__(self, host, port, timeout):
            assert (host, port) == ("127.0.0.1", 11434)
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return self
        def read(self, size):
            return b"x" * size
        def close(self):
            pass
    monkeypatch.setattr(local_provider.http.client, "HTTPConnection", Connection)
    with pytest.raises(TransportError):
        local_provider.local_request("/api/chat", {}, 1)
    Connection.status = 200
    with pytest.raises(TransportError):
        local_provider.local_request("/api/chat", {}, 1)


def test_truncated_local_generation_keeps_usage_and_does_not_retry(monkeypatch, data_root):
    def local(path, body, timeout):
        if path == "/api/show":
            return {"model_info": {"x": 1}}
        return {"done": True, "done_reason": "length", "prompt_eval_count": 5, "eval_count": 128}
    monkeypatch.setattr(local_provider, "local_request", local)
    config = RunConfiguration(provider="ollama", model="test-model")
    task = load_task(data_root / "repair", "clamp")
    with pytest.raises(ProviderFailure) as error:
        local_provider.make_local_provider(config).propose(RepairRequest(task))
    assert len(error.value.calls) == 1
    assert error.value.calls[0].usage.output_tokens == 128
