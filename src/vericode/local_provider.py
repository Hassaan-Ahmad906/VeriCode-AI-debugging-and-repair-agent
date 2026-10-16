"""Free local Ollama inference. Fixed loopback target, no proxies or redirects."""

import http.client
import json

from vericode.checkpoints import decode_json
from vericode.model_calls import RawCompletion, StructuredProvider, TransportError
from vericode.model_io import Usage
from vericode.schemas import ValidationError

LOCAL_PORT = 11434
MAX_BODY = 262_144


def local_request(path, payload, timeout):
    connection = http.client.HTTPConnection("127.0.0.1", LOCAL_PORT, timeout=timeout)
    try:
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            raise TransportError("Local server rejected the request")
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise TransportError("Local response exceeded its byte limit")
        return decode_json(body)
    except (OSError, ValueError, http.client.HTTPException):
        raise TransportError("Local model unavailable or invalid response") from None
    finally:
        connection.close()


def require_local_model(model, timeout):
    if not isinstance(model, str) or any(c in model for c in ("/", "\\", "@")) or "cloud" in model.lower():
        raise ValidationError("Use an installed local Ollama model tag; cloud aliases and URLs are disabled")
    info = local_request("/api/show", {"model": model}, timeout)
    if not isinstance(info, dict) or info.get("remote_host") or info.get("remote_model"):
        raise TransportError("Cloud-backed model aliases are disabled")
    if not isinstance(info.get("model_info"), dict) or not info["model_info"]:
        raise TransportError("A locally installed model with model_info is required")


class OllamaTransport:
    # Here offline means inference stays on this machine. Unlike a mock it uses
    # loopback HTTP; the server must also be started with OLLAMA_NO_CLOUD=1.
    offline = True

    def complete(self, prompt, *, model, max_output_tokens, timeout_seconds):
        # Qwen's byte-level tokenizer cannot need more text tokens than UTF-8
        # bytes. Reserve output and chat framing to avoid server-side truncation.
        if len(prompt.encode("utf-8")) + max_output_tokens + 256 > 4096:
            raise TransportError("Local prompt/output exceeds the conservative 4096-token context allowance")
        require_local_model(model, timeout_seconds)
        payload = json.loads(prompt.split("\n\n", 1)[1])
        task = payload.get("task", payload)
        if prompt.startswith("Propose up to eight"):
            schema = {"type": "object", "properties": {"cases": {"type": "array", "minItems": 1, "maxItems": 8,
                      "items": {"type": "object", "properties": {"args": {"type": "array"}, "expected": {}},
                                "required": ["args", "expected"], "additionalProperties": False}}},
                      "required": ["cases"], "additionalProperties": False}
        else:
            schema = {"type": "object", "properties": {
                "task_id": {"type": "string", "const": task["task_id"]},
                "target_file": {"type": "string", "const": "solution.py"},
                "replacement_source": {"type": "string", "minLength": 1, "maxLength": 32768}},
                "required": ["task_id", "target_file", "replacement_source"], "additionalProperties": False}
        result = local_request("/api/chat", {
            "model": model, "stream": False, "format": schema, "keep_alive": "5m",
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_predict": max_output_tokens,
                        "num_ctx": 4096, "num_thread": 4},
        }, timeout_seconds)
        if not isinstance(result, dict) or result.get("done") is not True:
            raise TransportError("Local generation was incomplete")
        usage = Usage(result.get("prompt_eval_count"), result.get("eval_count"), 0.0)
        if result.get("done_reason") == "length":
            raise TransportError("Local output-token ceiling reached", usage=usage)
        message = result.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise TransportError("Local response has no text", usage=usage)
        return RawCompletion(message["content"], usage, result.get("model"))


def make_local_provider(config):
    return StructuredProvider(OllamaTransport(), provider="ollama", model=config.model, limits=config.generation)
