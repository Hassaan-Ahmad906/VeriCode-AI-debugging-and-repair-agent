# Progress

## 2026-10-09 — Day 1

Inspection: empty directory; no applicable `AGENTS.md`, Git history, remotes, or
user changes. Python 3.13.5 and Git 2.52.0 are available; pytest was not installed.
Docker CLI 29.7.2 exists, but reading its user configuration was denied by the
sandbox. Daemon availability and isolation are unverified. Candidate execution
will remain mock-only today. Git was initialized with the existing configured
default branch (`master`) and existing Git identity unchanged.

### Task 1 — Package and CLI

- Added a dependency-free runtime package, pinned build/test dependencies,
  command-line entry point, setup documentation, seven-session plan, and ignores.
- Checks passed: editable installation with development dependencies, module CLI
  help, installed console entry point (`0.1.0`), pytest availability (`8.4.2`),
  and `pip check`. Dependency download required approved network access.
- The user supplied `https://github.com/Hassaan-Ahmad906/VeriCode-AI-debugging-and-repair-agent.git`.
  `git ls-remote --symref` succeeded with no refs: the remote is empty, so it has
  no advertised default branch. Keep the local configured default, `master`.
- Commit `386b470` pushed to `origin/master`; verified the remote SHA matches.
  Git metadata writes require approved elevated commands. A command-local
  `safe.directory` exception handles sandbox/user ownership differences without
  changing global Git settings or identity.

### Task 2 — Validated schemas and fixtures

- Added immutable task/candidate schemas, execution/evaluation result contracts,
  bounded JSON loading, fixed manifests, and three self-authored development tasks.
- Repair and evaluation assets have separate loaders. Repair objects contain no
  evaluator paths or tests. Final-task manifest is intentionally empty.
- Checks: `python -m pytest -q --tb=short` — 33 passed. Tests cover malformed data,
  unsafe targets/IDs, oversized JSON, duplicate fields, split/version consistency,
  and false mock-success claims. Long test parameter IDs initially broke Windows
  test setup; explicit short IDs fixed the issue. No candidate code was executed.
- Reviewed fixture arithmetic and specifications manually. Runtime fixture
  behaviour remains unverified until the Day 2 sandbox exists.
- Commit `217e150` pushed to `origin/master`; verified the remote SHA matches.

### Task 3 — Offline mock pipeline

- Added a provider-neutral contract, scripted mock provider, constrained full-file
  patch validation, disposable staging workspace, mock executor/evaluator, and JSON
  artifacts. CLI commands list tasks and run demonstrations. No candidate/test code
  executes, and environment configuration cannot enable a paid provider.
- Checks: `python -m pytest -q --tb=short` — 49 passed; installed console help,
  task listing, saved CLI demo, and `pip check` passed. Diff whitespace and secret
  pattern review passed. Ignored environments/caches/artifacts were not staged.
- Tests verify source preservation, cleanup after success/errors, evaluator load
  order and provider input fields, malicious side-effect text remaining inert,
  unknown-task errors, no credential logging, and refusal to overwrite artifacts.
- Demo artifact: `artifacts/day1-clamp.json` (local, ignored). It records a mock
  result, zero API cost, unknown tokens, and no measured test outcomes.
- This entry is included in the Task 3 commit, titled
  `feat: add offline mock repair pipeline and JSON demo`. Find its hash with
  `git log --oneline -3`; push verification is reported at session completion.

### Day 1 completion and next-session starting point

All three Day 1 acceptance criteria are met. No paid calls or candidate execution
occurred. There are no measured repair results, approved sandbox runner, external
benchmark, or final evaluation tasks. Current automated checks test the controller,
not the runtime correctness of fixture code. No release tag was created.

Stop here; do not begin Day 2 automatically. At the start of Day 2:

1. Read this log, inspect Git status/remotes, and run the existing offline tests.
2. Check Docker daemon access and Linux-container support. Its CLI alone was
   detected on Day 1; configuration access was blocked inside the sandbox.
3. Implement the bounded Docker runner with no network, non-root user, resource
   limits, read-only root, bounded workspace/output, no inherited secrets or host
   mounts, and full-job termination/cleanup. Retain mock-only execution if an
   approved sandbox is unavailable.
4. Verify trusted completion/exception/timeout cases and isolation before allowing
   any candidate execution. Keep evaluation assets out of repair jobs.

Commands from the repository root (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\vericode.exe list-tasks
.\.venv\Scripts\vericode.exe demo --task clamp
```

Understanding checks: Why are tokens null in a mock run? How do withheld tests
differ from a final task split? Why is a temporary workspace not a sandbox?

## 2026-10-11 — Day 2

Inspection: clean `master`, unchanged verified GitHub remote, and no applicable
`AGENTS.md`. Day 1 final commit `918c3c4` is present locally and on GitHub. All 49
existing checks passed. Docker Desktop was stopped; starting it in the background
made the Linux engine available (Docker 29.7.2, WSL2, cgroup v2, default seccomp,
reported CPU/memory/swap/PID support). No existing containers were changed.

### Task 1 — Bounded Docker runner

- Added a digest-pinned Python image, version-pinned pytest dependencies, a trusted
  parent harness, validated resource limits, pre-start policy inspection, bounded
  controller subprocesses, and Docker-only execution. No host directories are
  mounted; only source and visible-test text cross the job boundary.
- Statuses distinguish assertions, collection errors, timeout, output/OOM limits,
  and infrastructure failure. Cleanup removes the full container and is verified.
- Checks: offline suite 61 passed, 4 Docker checks skipped; explicitly requested
  runner checks 13 passed, including four live Docker cases (completion, exception,
  collection error, timeout). Cleanup was confirmed for each live job.
- Elevated pytest encountered a cache ownership warning; later elevated checks
  disable pytest's cache provider. It did not affect test outcomes.
- Container policy follows the official Docker documentation linked in
  `docs/sandbox.md`. Read the documented timing and pytest-integrity limitations.
- Task 1 is recorded in the commit `feat: add bounded Docker candidate execution`;
  its SHA and push verification follow in the next task entry.

Next: Task 2 — immutable visible-job inputs, CLI execution/results, and checks for
output overflow, workspace safety, and cleanup failure handling.
