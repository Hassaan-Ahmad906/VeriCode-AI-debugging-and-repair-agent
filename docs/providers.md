# Structured model boundary

`model_io.py` defines requests, responses, generation limits, and usage. The
existing `providers.py` API remains available. `model_calls.py` wraps a trusted
transport and validates its model-produced JSON. MockProvider uses that same
boundary with a deterministic JSON transport; no hosted model adapter exists.

The transport receives one string containing only the specification, original
source, repair-visible tests, and task metadata, plus a configured model identifier,
output-token limit, and request timeout. It has no model-controlled filesystem,
shell, evaluator context, or tool access. Transports are trusted controller code;
the offline flag is a declared contract, not a network security boundary.

Defaults: 64 KiB prompt, 64 KiB response, 2048 requested output tokens, at most
three transport calls, and a 15-second request timeout. Prompt bytes are checked
before sending. Response bytes and reported output-token overruns are rejected.
Byte limits are not token counts. Future SDK adapters must enforce the supplied
network timeout and streaming/body limits; this wrapper cannot forcibly stop
arbitrary blocking Python adapter code. No such live adapter is enabled today.

Only explicitly transient transport errors can retry. Each retry uses exactly the
same prompt and options. Malformed JSON, duplicate/unknown fields, forbidden
targets, missing fields, non-finite values, and invalid usage cannot trigger a
second repair response. This preserves strategy A's one-response definition.

Usage is attached to every actual call, including retryable/permanent failures
when an adapter can provide it. Transport exceptions are logged with a safe status,
not raw exception messages that could contain credentials. Successful responses
record a hash, configured/reported model identifiers, and observed controller
latency. Tokens and cost remain null when unknown. Known subtotals are separate;
an unknown billed call makes the total cost unknown even if another call is priced.
Mock calls have known zero API cost and unknown tokens.

Limits and usage records are engineering controls, not a dollar-budget mechanism.
Network/paid transports are rejected before any call. Setting credentials or a
spending-cap environment variable does not enable them. A future live adapter
requires explicit budget configuration, verified pricing, conservative spending
enforcement, and tests before a pilot. No model/provider SDK dependency is added.
