# VeriCode

VeriCode is a local, research-oriented Python program-repair project. It asks:
**How much do execution feedback and additional test generation improve
LLM-based program repair, relative to their cost?**

The planned comparison is direct repair (A), feedback-guided repair (B), and
test-augmented repair (C). Calls and tokens will be reported separately; a shared
upper budget does not make these methods compute-matched.

## Status

Day 4 is in progress: direct repair A, feedback-guided repair B, structured mock
completions, per-call usage, bounded Docker execution, and resumable batches work.
Paid API execution is disabled. No live-model experiment
or final evaluation has been performed. See [PLAN.md](PLAN.md) and
[PROGRESS.md](PROGRESS.md) for acceptance criteria and the next session.
Day 4's feedback-loop checks are being completed; the Day 3 suite passed 153 checks.

## Setup

Requires Python 3.11+ (developed on Python 3.13.5) and Git. Run from the repository
root. The runtime package has no third-party dependencies. Build and direct test
dependencies are pinned in `pyproject.toml`; this is not a complete transitive lock.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m vericode --help
.\.venv\Scripts\vericode.exe --version
```

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m vericode --help
```

Installation may need internet access; the Day 1 workflow itself is offline.
`.env.example` documents future configuration names, with no credentials.
No live model adapter is enabled or implemented yet.

Run the controller tests and an offline demonstration:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\vericode.exe list-tasks
.\.venv\Scripts\vericode.exe demo --task clamp
# Optional: save a new artifact. Choose an unused filename for each run.
.\.venv\Scripts\vericode.exe demo --task sum_positive --output artifacts/demo.json
```

The demo prints JSON with the replacement source, a unified diff preview, the
recorded repair prompt, metadata, and usage. It stages the patch in a fresh
temporary directory and cleans up afterward. The original fixture is unchanged.
The diff is a display artifact; the validated full-file replacement is canonical.
`--data-root` lets you point at this repository's `data` directory from elsewhere.
Fixture data is not bundled inside the installed Python package.

Expect `run_kind: "mock"`, execution status `"not_executed"`, and
`evaluation.suite_passed: null`. One **mock provider invocation** is logged; no
hosted model is called. Token counts are unavailable, while API cost is known to
be zero. UUIDs and timestamps vary; scripted patches are deterministic. Existing
output files are never overwritten. Local JSON artifacts are ignored by Git.

The [fixture format](data/README.md) separates repair-visible and evaluator-only
data. These checks validate the controller and data; they do not run candidate
functions on the host.

## Run visible tests in Docker

Start Docker Desktop with its Linux engine (cgroup v2), then build the trusted
image. Rebuild it after changing or pulling updated harness source:

```powershell
docker build --tag vericode-runner:day2 sandbox
.\.venv\Scripts\python.exe -m vericode sandbox-info
# Original clamp fixture: one visible test fails (exit code 1).
.\.venv\Scripts\python.exe -m vericode run-tests --task clamp --backend docker
# Scripted mock patch: both visible tests pass (exit code 0).
.\.venv\Scripts\python.exe -m vericode run-tests --task clamp --candidate mock --backend docker
```

`run-tests` defaults to mock execution when `--backend docker` is omitted. Docker
unavailability is an infrastructure error (exit code 2), with no host fallback.
`--timeout 5` sets the attached execution deadline. `--output artifacts/check.json`
saves a new JSON record; choose an unused filename. Each record includes observed
counts/output, cleanup confirmation, image ID, limits, and source/test hashes.
The command only loads repair-visible data; its `evaluation` field is null.

These are development smoke checks. `--candidate mock` uses a scripted response
and spends no API money. Visible-test success does not establish correctness on
the separate evaluator suite. The original sum/vowel fixtures deliberately have
visible examples that miss their bugs.

Explicitly run trusted Docker integration checks:

```powershell
.\.venv\Scripts\python.exe -m pytest --run-docker -q
```

Docker checks are skipped by default, but fail when explicitly requested without
a working engine/image. See [sandbox controls and limitations](docs/sandbox.md).
The runner has been verified on Docker Desktop 29.7.2 with its WSL2 Linux engine.
Other environments must pass their own explicitly requested checks.

## Scope and safeguards

Direct repair A makes one proposal, then observes visible tests without sending
feedback to the model or requesting a revision:

```powershell
# Fully offline: patch ready, test outcomes unknown.
.\.venv\Scripts\python.exe -m vericode repair --task clamp
# Scripted mock response, followed by actual visible tests inside Docker.
.\.venv\Scripts\python.exe -m vericode repair --task clamp --backend docker --output artifacts/direct.json
```

Choose an unused output filename. `--model` records the configured provider model
identifier; with the mock provider it is a label for the same scripted responses.
`--max-model-calls` bounds transport attempts (1-3), while malformed responses
stop after their first answer. `--max-output-tokens` bounds the requested output.
Every call, including failed transport calls with available usage, is logged.
Unknown totals stay null; known subtotals are separate. The request timeout is an
adapter contract. See [provider boundary](docs/providers.md).

`agent_accepted` describes the controller's visible-suite decision. It is true for
visible passes, false for rejected/failed patches, and unknown for mock or
unresolved execution. `evaluation` remains null until the independent evaluator
is implemented. The `demo` command retains its original mock-only demonstration.

Run all development tasks with a fixed configuration, then resume:

```powershell
.\.venv\Scripts\python.exe -m vericode batch --run-dir artifacts/my-direct-batch
.\.venv\Scripts\python.exe -m vericode batch --run-dir artifacts/my-direct-batch --resume
```

The supplied [configuration](configs/offline_direct.json) selects mock models and
mock execution. Completed outcomes are preserved, including failures; the second
command adds zero calls after a finished run. Configuration, task, or runtime
changes are rejected. Logs contain prompts, patches, call usage, and execution
states. Read [checkpoint and recovery behaviour](docs/checkpoints.md) before
resuming an interrupted run.

Strategy B runs the original visible suite before proposing, then revises using
only the latest source and bounded visible feedback:

```powershell
# Offline: one scripted candidate; no measured feedback or acceptance.
.\.venv\Scripts\python.exe -m vericode feedback --task clamp
# Docker: original clamp fails; the scripted candidate passes two visible tests.
.\.venv\Scripts\python.exe -m vericode feedback --task clamp --backend docker --output artifacts/feedback.json
# Fixed offline B batch, followed by resume with zero new calls.
.\.venv\Scripts\python.exe -m vericode batch --config configs/offline_feedback.json --run-dir artifacts/my-feedback-batch
.\.venv\Scripts\python.exe -m vericode batch --config configs/offline_feedback.json --run-dir artifacts/my-feedback-batch --resume
```

B defaults to at most three repair attempts and six total transport calls, with
at most three calls per attempt. Set `--max-attempts`, `--max-model-calls`, and
`--max-transport-calls` separately. `--feedback-bytes` caps visible output sent to
each request. Records retain the initial observation, every prompt/proposal/check,
and globally numbered calls. Malformed answers or patches stop without executing
them; repeated exact source stops without another execution. Previously observed
source, including the original, counts as repeated. Timeouts, resource limits,
output limits, and test errors may inform a bounded revision; infrastructure or
unconfirmed cleanup stops immediately.

An already-passing original returns unchanged with zero calls. The sum/vowel
fixtures demonstrate why this is only visible-suite acceptance: their visible
tests miss the bug. B configuration and records use schema 2; A retains schema 1.
Use a new batch directory after code/configuration changes; old Day 3 snapshots
remain preserved and can reject resume because their runtime fingerprint differs.

Start with small, single-file Python functions and self-authored development
fixtures. Repair-visible tests and evaluation-only tests are separate inputs.
The agent must never receive reference implementations, evaluator paths, or
evaluation-only tests and feedback during repair.

Candidate code and generated tests are untrusted. Never execute them on the host.
The demo simulates execution; `run-tests --backend docker` explicitly uses the
constrained runner. If Docker is unavailable, use the mock command. Container isolation
reduces risk but does not guarantee security. This project is local-only and must
not be deployed as a public arbitrary-code execution service.

This project makes no claim of novelty, publication readiness, or guaranteed
internship outcomes. A future patch may pass an evaluation suite without being
proven correct.

Read [architecture](docs/architecture.md), the [draft experiment protocol](docs/experiment_protocol.md),
[limitations](docs/limitations.md), and [learning notes](docs/learning_notes.md).
Strategy C, budgeted API adapters, independent evaluation, benchmark
integration, analysis, and the UI are later sessions. This is not a release-ready system.
