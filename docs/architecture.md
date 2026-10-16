# Architecture

Current entry points are the CLI and optional local Streamlit workspace.
`ui_service.py` dispatches the same repair/scoring controllers; `workspace_ui.py`
renders workbench, session history, model settings, training and evidence screens.
`providers.make_provider` selects scripted mocks or the fixed-loopback local
Ollama adapter. The latter requests structured JSON and reports actual usage;
hosted paid adapters remain disabled. Frozen demonstration studies/batches remain
mock-only so historical claims cannot silently become live-model measurements.
`training_data.py` and the separate Colab scripts prepare optional free-GPU LoRA
customization. They do not load benchmark/evaluator data or execute generated code.
The day-by-day sections below document how the system reached this architecture.

The host controller loads repair-visible JSON into a frozen `RepairTask`.
It contains the specification, original source, visible tests, and one canonical
filename, `solution.py`. The loader reads bounded data; it never imports fixture
code. Unknown fields are rejected so evaluator fields cannot slip into the
repair-input contract.

`schemas.py` defines repair tasks and replacement candidates. `datasets.py` loads
repair inputs and fixed manifests. `results.py` distinguishes execution states
and nullable evaluation outcomes. `evaluation.py` separately loads evaluator
tests; future orchestration must call it only after repair is complete.

Day 1 flow: `cli.py` → `experiments.py` → `repair.py` → `ModelProvider.propose` →
`patches.py` → fresh staging directory → `MockExecutor` → chosen candidate.
Only then does the controller load the separate evaluation suite and record a
mock evaluation. `experiments.py` writes JSON with the prompt, patch, data version,
HEAD commit when available, usage, configuration, and explicit limitations.

`providers.py` defines the typed provider protocol and a deterministic mock.
The request contains only the allowlisted repair task. Canned mock responses are
demonstration configuration, not independently verified reference solutions.
`patches.py` checks task identity, the sole target, parseable Python, and the entry
function. Parsing does not prove code safe, executable, or semantically correct.
The provider is a trusted host-side adapter; the model itself has no file tools.

The staging directory is a host-side text workspace, **not an execution sandbox**.
It contains only `solution.py` and visible tests and is deleted on success or
exceptions. Mock execution does not import or run either file. The only subprocess
in the mock flow is a fixed Git HEAD metadata query, with a two-second timeout and
no candidate-controlled arguments. Its trust exception is limited to the editable
package's repository path.

Future flow adds sandbox execution, visible feedback, and bounded revisions before
final independent evaluation. Evaluation feedback never returns to the provider.

Day 1 separates data by API and object shape, not operating-system permissions.
The trusted controller can read both fixture trees. The model will have no shell
or filesystem tools. The Docker runner sends only approved source/visible-test
contents over stdin, never the repository root, evaluation directory during
repair, or credentials.

## Day 2 execution path

`jobs.py` creates an immutable `VisibleJob` from a task and optional validated
candidate. The executor receives two strings, not paths or evaluator objects.
`DockerExecutor` preflights daemon capabilities, resolves a local image ID,
creates and inspects a constrained job, and starts its trusted image harness.
The harness stages text on container tmpfs and runs pytest in a child with a fixed
environment. `processes.py` drains output with a hard retention limit and deadline.
Host and independent in-container deadlines bound execution. Cleanup removes the
whole container. An unconfirmed cleanup blocks that executor
from submitting more jobs.

`run-tests` serializes an engineering smoke-check record. `sandbox-info` verifies
prerequisites without executing candidate code. The older `demo` command remains
mock-only. Final evaluator orchestration comes later.

## Day 3 direct repair

`model_io.py` separates provider contracts from adapters; `model_calls.py` bounds
transport attempts and validates JSON. MockProvider uses this same path. The
request exposes only repair-visible task fields. Call records distinguish
configured/reported model IDs, unknown usage, known subtotals, and failures.

`strategies.py` implements A: propose once, validate the sole replacement target,
then create a visible job. No execution occurs before proposal; no observations
feed back to the provider. `run_config.py` records limits, backend, and provider
selection. `direct_run.py` emits the patch, one attempt history, call ledger, and
post-response visible outcomes. Invalid responses and invalid patches are separate.
Default executor is mock; Docker is an explicit selection. Neither path loads
evaluation assets. Strategy C uses the same repair core after validating test proposals.

`batch.py` coordinates sequential tasks from an immutable manifest/configuration.
`checkpoints.py` owns bounded JSON/JSONL persistence, checksums, and a directory
lock. A durable start precedes model generation; a durable terminal event contains
the outcome. Resume validates fingerprints and skips recorded outcomes without
regenerating patches. Unknown starts and unconfirmed cleanup block replay. The
batch stops on infrastructure failure and retains it as an outcome. Docker uses
one frozen image ID for all pending tasks.

## Day 4 feedback repair

`feedback.py` implements B in plain Python. Initial visible execution precedes
the first request; each revision receives the latest source and a bounded
allowlist of visible status, counts, and test output. Controller details, job and
image identities, and runner protocol frames are excluded. Test output remains
untrusted data. No evaluator input or filesystem capability enters this request.

Each request can use transport retries, capped by both provider limits and the
remaining total call budget. Repair attempts and actual calls are distinct;
call indices are global within the task. Every request and observed candidate
execution is retained in typed history. Mock execution proposes once and stops
with unknown acceptance; it cannot supply measured feedback. Existing direct
request prompts and the order of strategy A remain unchanged.

## Day 5 augmentation and evaluation

`generated_tests.py` validates JSON cases against bounded specification rules and
renders accepted assertions as literals. `augmented.py` charges generation calls
before invoking B with the remaining budget and augmented repair-visible tests.
Schema 3 records retain every accepted/discarded case and globally indexed usage.

`benchmark.py` verifies frozen repair data without reading evaluator files. Pinned
upstream references live under the audit-only data tree. `scoring.py` validates a
completed repair record, then loads the separate frozen evaluation suite. It runs
original and candidate source through the same isolated executor, never calls a
provider, and emits a separate score record. `metrics.py` retains unknown outcomes
and explicit denominators. `records.py` bounds saved-record input to 16 MiB.

## Day 6 studies and reporting

`protocol.py` freezes validated zero-cost configurations, task/source identities,
prompt/oracle versions and immutable image IDs before collection. `study.py`
records each repair phase outcome before any scoring phase, reusing durable
checkpoint safeguards without model access to evaluator data. Scores link to
exact repair hashes. Historical snapshots are intentionally preserved.

`analysis.py` checks evidence bytes/links and reconciles call-ledger totals, then
exports a complete expected task matrix, per-protocol/split/method summaries,
failure-case links, and optional Matplotlib figures. No model or candidate is
executed during analysis. Unknowns and incomplete work remain explicit.
