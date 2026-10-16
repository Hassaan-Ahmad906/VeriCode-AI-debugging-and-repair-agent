"""Bounded structured completions; transport retries do not revise a repair."""

from dataclasses import dataclass
import hashlib
import json
from time import monotonic
from typing import Protocol
from collections.abc import Callable

from vericode.datasets import _unique_object
from vericode.model_io import CallRecord, GenerationLimits, ModelResponse, RepairRequest, Usage, identifier
from vericode.schemas import Candidate, ValidationError


@dataclass(frozen=True)
class RawCompletion:
    text: str
    usage: Usage = Usage()
    model: str | None = None


@dataclass(frozen=True)
class StructuredReply:
    value: object
    model: str
    usage: Usage
    calls: tuple[CallRecord, ...]


class CompletionTransport(Protocol):
    offline: bool

    def complete(self, prompt: str, *, model: str, max_output_tokens: int,
                 timeout_seconds: float) -> RawCompletion: ...


class TransportError(RuntimeError):
    """Adapters must supply known usage even when a request fails."""

    def __init__(self, message: str = "transport error", *, usage: Usage = Usage()):
        super().__init__(message)
        self.usage = usage


class TransientTransportError(TransportError):
    """A retryable connection/rate-limit failure, not an invalid model answer."""


class ProviderFailure(RuntimeError):
    def __init__(self, code: str, calls: tuple[CallRecord, ...], detail: str):
        super().__init__(detail)
        self.code = code
        self.calls = calls


def _reject_constant(value: str):
    raise ValidationError("response JSON contains a non-finite number")


def provider_enabled(provider):
    if getattr(provider, "offline", False) is True:
        return True
    from vericode.hosted_provider import BudgetedProvider
    return isinstance(provider, BudgetedProvider)


def parse_candidate(text: str, byte_limit: int) -> Candidate:
    try:
        if not isinstance(text, str) or len(text.encode("utf-8")) > byte_limit:
            raise ValidationError("model response exceeds its text/byte contract")
        data = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        return Candidate.from_dict(data)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError(f"invalid structured candidate: {exc}") from exc


class StructuredProvider:
    def __init__(self, transport: CompletionTransport, *, provider: str, model: str,
                 limits: GenerationLimits | None = None):
        identifier(provider, "provider")
        identifier(model, "model")
        self.transport = transport
        self.provider = provider
        self.model = model
        self.limits = limits or GenerationLimits()
        self.offline = transport.offline is True

    def propose(self, request: RepairRequest, *, max_transport_calls: int | None = None) -> ModelResponse:
        reply = self.generate(request, parse_candidate, max_transport_calls=max_transport_calls)
        return ModelResponse(reply.value, self.provider, reply.model, reply.usage.input_tokens,
                             reply.usage.output_tokens, reply.usage.cost_usd, reply.calls)

    def generate(self, request: RepairRequest, parser: Callable, *, max_transport_calls: int | None = None) -> StructuredReply:
        if not provider_enabled(self):
            raise ProviderFailure("paid_execution_disabled", (), "Paid/network model execution is disabled; configure a budgeted adapter first.")
        call_limit = self.limits.max_transport_calls
        if max_transport_calls is not None:
            if type(max_transport_calls) is not int or not 1 <= max_transport_calls <= call_limit:
                raise ValidationError("remaining transport calls: expected a positive limit within provider limits")
            call_limit = max_transport_calls
        prompt = request.prompt()
        if len(prompt.encode("utf-8")) > self.limits.prompt_bytes:
            raise ProviderFailure("input_limit", (), "Repair prompt exceeds the configured byte limit before any model call.")
        calls = []
        for index in range(1, call_limit + 1):
            started = monotonic()
            try:
                raw = self.transport.complete(prompt, model=self.model,
                                              max_output_tokens=self.limits.output_tokens,
                                              timeout_seconds=self.limits.request_timeout_seconds)
            except Exception as exc:
                retryable = isinstance(exc, TransientTransportError)
                usage = exc.usage if isinstance(exc, TransportError) and isinstance(exc.usage, Usage) else Usage()
                status = "transient_error" if retryable else "transport_error"
                calls.append(CallRecord(index, status, self.provider, self.model, None, usage, monotonic() - started))
                if retryable and index < call_limit:
                    continue
                raise ProviderFailure(status, tuple(calls), "Model transport failed; details are omitted to avoid logging credentials.") from None
            usage = raw.usage if isinstance(raw, RawCompletion) and isinstance(raw.usage, Usage) else Usage()
            reported = None
            digest = None
            try:
                if not isinstance(raw, RawCompletion) or not isinstance(raw.usage, Usage):
                    raise ValidationError("adapter did not return a RawCompletion with validated Usage")
                if raw.model is not None:
                    identifier(raw.model, "reported model")
                    reported = raw.model
                if usage.output_tokens is not None and usage.output_tokens > self.limits.output_tokens:
                    raise ValidationError("reported output tokens exceed the request limit")
                value = parser(raw.text, self.limits.response_bytes)
                digest = hashlib.sha256(raw.text.encode("utf-8")).hexdigest()
            except (ValidationError, TypeError) as exc:
                calls.append(CallRecord(index, "invalid_response", self.provider, self.model, reported, usage, monotonic() - started))
                raise ProviderFailure("invalid_response", tuple(calls), str(exc)) from None
            calls.append(CallRecord(index, "completed", self.provider, self.model, reported, usage, monotonic() - started, digest))
            return StructuredReply(value, reported or self.model, usage, tuple(calls))
        raise AssertionError("validated transport-call budget cannot be empty")
