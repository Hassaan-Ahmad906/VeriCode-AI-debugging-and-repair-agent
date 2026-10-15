# Frozen offline studies

The current study tool collects pipeline demonstrations, not measured LLM results.
It accepts only the mock provider, an explicit zero-dollar cap, disabled paid
execution, null seed, and the same model, per-response generation limits and
sandbox controls across A/B/C. Calls differ by method and are not compute-matched.
Hosted pricing, live SDK adapters, and enforceable paid spending are absent.

Freeze before collection, choosing unused paths:

```powershell
.\.venv\Scripts\python.exe -m vericode study freeze --config configs/study_mock.json --split development --output artifacts/new-protocol.json
.\.venv\Scripts\python.exe -m vericode study run --protocol artifacts/new-protocol.json --run-dir artifacts/new-study
.\.venv\Scripts\python.exe -m vericode study run --protocol artifacts/new-protocol.json --run-dir artifacts/new-study --resume
```

For an actual sandbox demonstration, start Docker and choose
`configs/study_docker.json` when freezing. `--split final` selects the pinned
three-task final subset; those repair mocks emit unchanged source, never reference
solutions. Development scripted repairs are controller fixtures. Both modes make
zero paid calls and must not be published as model-performance measurements.

The frozen protocol records Git HEAD, raw runtime/harness fingerprint, fixed
manifest and task hashes, separate evaluator-freeze identity, model identifiers,
generation/execution/attempt/call limits, prompt/oracle versions, available seed,
and resolved immutable Docker image. Checksums detect corruption, not authenticity.
Runtime/data/config changes require a new protocol and run directory. A docs-only
commit can change HEAD without changing the recorded runtime; both remain logged.

Collection persists a start/outcome for every strategy/task repair, then performs
all scoring in a second phase. No evaluator suite opens during the repair phase.
The journal envelopes carry nested repair/score payloads and individual checksums.
Every request/candidate/usage entry remains in the repair payload; evaluator outputs
stay in scores and are never passed to providers. Original and candidate are
checked separately on the same independent suite.

Completed outcomes, including failures, are skipped on resume. A completed study
adds zero calls and needs no Docker access. A task started without a durable outcome
is uncertain and blocks replay, even in the scoring phase. Infrastructure errors
halt collection; unconfirmed cleanup blocks pending jobs. Preserve affected logs;
there is no automatic stale-lock recovery, retry of completed failures, exactly-once
remote-call guarantee, or silent missing-result replacement. A 16 MiB event and
64 MiB journal ceiling reserves capacity before any task starts.

Pilot procedure: run the development pipeline, inspect cleanup/usage/errors and
saved prompts, then freeze a separate final protocol only after that review. The
final demo tests collection and failure reporting on public adapted tasks. For any
future paid study, implement/test conservative priced caps and obtain explicit
funding configuration first, verify provider prices, and freeze a new protocol.
