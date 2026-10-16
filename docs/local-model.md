# Free CPU inference

The optional Ollama adapter calls a locally installed model on
`127.0.0.1:11434`. It needs no API key and makes no paid API calls. It does not
pull a model automatically. The first model download needs internet; inference
can then run locally. This is a pretrained model, not a model trained by VeriCode.

The Windows helper `python scripts/setup_local_model.py` downloads a pinned
official portable runtime, verifies the release SHA-256, and extracts CPU files
under ignored `artifacts/local-model/runtime`. Weights and downloads are never
committed. The hash identifies the official asset, not a complete security audit.
Use `scripts/start-local-model.ps1` to launch the workspace runtime on loopback,
with cloud disabled, one loaded model and one request at a time. Logs and model
storage remain under ignored workspace artifacts. No system installation is made.

Pull a small CPU model once, from a second PowerShell terminal:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11434'
.\artifacts\local-model\runtime\ollama.exe pull qwen2.5-coder:1.5b
```

In the UI select provider `ollama`, set the installed model tag, select `docker`
execution and run repair. The UI also accepts a custom function, specification
and visible pytest tests. Custom inputs support A/B; C requires an independently
reviewed expected-value oracle, and no frozen independent evaluator is available
for arbitrary pasted code. Finite visible-test success is not proof.

CLI equivalent on a repository fixture:

```powershell
.\.venv\Scripts\python.exe -m vericode repair --provider ollama --model qwen2.5-coder:1.5b --backend docker --max-output-tokens 512 --request-timeout 30 --output artifacts/local-repair.json
```

Model tags are configurable. Use a smaller model or warm the installed model if
the CPU cannot answer within 30 seconds; errors never switch to a hosted provider
or host execution. The local HTTP client has a socket timeout and bounded body;
it cannot forcibly stop inference already running inside the trusted server.
No automatic retry follows a local HTTP failure. The server may finish abandoned
work. Its inference is separate from the sandbox deadline for candidate execution.

The adapter requests a strict JSON schema with the permitted candidate fields
(or data-only cases for C), then independently validates the result as usual.
An earlier JSON-only local smoke attempt copied task fields and was rejected;
structured decoding is an adapter control, not evidence of source correctness.
The adapter uses a fixed numeric loopback address, bypasses proxy environment
variables and never follows redirects. Cloud tags, URLs and reported remote
aliases are rejected; start the server with `OLLAMA_NO_CLOUD=1` as an additional
control. Model metadata is checked before each completion. `offline=True` means
no remote inference in this adapter; it still communicates over local HTTP.

CPU defaults: 4 threads, context 4096, temperature 0 and one response at a time.
Input UTF-8 bytes plus output-token limit plus a framing reserve must fit context,
using a conservative bound for Qwen's byte-level tokenizer. Other tokenizers are
not verified; use this adapter with reviewed Qwen-family models. Reported token
counts come from Ollama; API cost is zero, excluding electricity/CPU time. Local
runs are labeled `local_model_smoke`; model tags are mutable and these are not a
frozen measured experiment. Historical mock-study analysis remains unchanged.

Hosted API settings are visible but disabled under the user's free-only policy.
API-key storage and paid hosted execution are not implemented. Do not enter keys
in chat or Git. A hosted adapter would need a selected provider/model, explicit
spending policy, verified pricing and conservative cost enforcement first.

Sources: [Ollama chat API](https://docs.ollama.com/api/chat),
[local-only cloud setting](https://docs.ollama.com/faq),
[Qwen2.5-Coder 1.5B](https://ollama.com/library/qwen2.5-coder:1.5b).
