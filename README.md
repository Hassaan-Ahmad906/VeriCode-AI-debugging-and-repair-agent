# VeriCode

VeriCode is a local, research-oriented Python program-repair project. It asks:
**How much do execution feedback and additional test generation improve
LLM-based program repair, relative to their cost?**

The planned comparison is direct repair (A), feedback-guided repair (B), and
test-augmented repair (C). Calls and tokens will be reported separately; a shared
upper budget does not make these methods compute-matched.

## Status

Day 1 is in progress: package and CLI foundation. Paid API execution is disabled.
No performance measurements have been collected. See [PLAN.md](PLAN.md) and
[PROGRESS.md](PROGRESS.md) for acceptance criteria and the next session.

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

## Scope and safeguards

Start with small, single-file Python functions and self-authored development
fixtures. Repair-visible tests and evaluation-only tests are separate inputs.
The agent must never receive reference implementations, evaluator paths, or
evaluation-only tests and feedback during repair.

Candidate code and generated tests are untrusted. Never execute them on the host.
Day 1 will simulate execution. Day 2 adds a constrained Docker runner; if a
suitable sandbox is unavailable, retain mock execution. Container isolation
reduces risk but does not guarantee security. This project is local-only and must
not be deployed as a public arbitrary-code execution service.

This project makes no claim of novelty, publication readiness, or guaranteed
internship outcomes. A future patch may pass an evaluation suite without being
proven correct.
