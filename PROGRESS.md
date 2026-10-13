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
- Commit `f8d435f` pushed to `origin/master`; remote SHA verified.

### Task 2 — Visible jobs, CLI results, and cleanup checks

- Added immutable text-only visible jobs, `sandbox-info`, and mock-by-default
  `run-tests` with explicit Docker selection. Logs capture image/limits, source
  hashes, observed counts/output, and cleanup state; they never load evaluation
  assets. Existing output is rejected before execution.
- Output floods terminate the container; capture is bounded. Empty/skipped suites
  and early exit without reports cannot count as success. Unconfirmed cleanup
  blocks further jobs on that executor. Invalid UTF-8 is rejected before execution.
- Checks: 72 offline tests passed, 11 Docker checks skipped; targeted Docker-enabled
  runner/job checks 25 passed. Coverage includes output flood, spawned descendants,
  workspace writes preserving the dataset, invalid reports, and cleanup failure.
- Windows temp-directory permissions affected both sandbox/elevated pytest runs.
  Tests now use an individually created disposable temp directory and disable
  cache writes; ordinary offline pytest passed afterward.
- CLI preflight passed. Saved smoke artifacts `artifacts/day2-clamp-original.json`
  (1 pass/1 failure, exit 1) and `artifacts/day2-clamp-mock-patch.json` (2 passes,
  exit 0). Both cleanup checks succeeded; zero API spend. These are ignored local
  engineering artifacts, not final evaluation or live-model measurements.
- Commit `4dd6a6b` pushed to `origin/master`; remote SHA verified.

### Task 3 — Verified isolation and fail-closed policy

- Added worker probes for UID/GID, capability sets, no-new-privileges, seccomp,
  network denial, absent sentinel host credentials/files/evaluator assets and
  controller paths, read-only root, bounded tmpfs, and actual cgroup settings.
- Process spawning hits the 32-PID limit; workspace filling hits ENOSPC; a large
  allocation is recorded as Docker OOM/resource limit. Jobs are removed afterward.
- Policy now rejects injected environment variables, changed harness/log settings,
  and unsupported cgroup versions. Decoded binary output obeys the configured cap.
- Added a trusted in-container Linux deadline, independent of the host watchdog;
  its check extends the host deadline and spawns a descendant. Timeout remains a
  separate outcome, and the full job is removed.
- An early environment probe omitted pytest's metadata variables; the assertion
  was corrected to include PYTEST_CURRENT_TEST/PYTEST_VERSION. A long delay also
  affected early test runs; those elapsed times are not experiment latency data.
  The final report supersedes the earlier failed isolation artifact.
- Final engineering report: `artifacts/day2-final-checks.xml` (ignored local file):
  104 passed, zero failures/errors/skips, including 17 explicit Docker checks.
  Saved XML counts were verified. Earlier ordinary offline checks passed with
  Docker cases skipped. `pip check`, whitespace review, and secret-pattern review
  passed. No VeriCode containers remained after the final suite.
- Final local runner image ID:
  `sha256:cd84127ea2c5412a54c1e6cd1a33021ecfef5d93ecbc233e1d3f2f3681fccd8f`.
  Compatibility label version 2 rejects earlier images lacking the container timer.
  Resource settings, requirements, and unverified guarantees are in `docs/sandbox.md`.
- Task 3 is recorded by `test: verify candidate isolation and independent execution deadlines`;
  its final hash/push verification is reported at session close. A commit cannot
  include its own final hash; use `git log --oneline -3` to see all Day 2 commits.

### Day 2 completion and Day 3 starting point

All three Day 2 acceptance criteria are implemented. Candidate code runs only in
the constrained Docker path; default CLI/tests remain mock/offline. No paid model
calls, external benchmarks, final evaluation, or release tag were used. Docker
verification is local engineering evidence, not a complete security guarantee.

Stop here; do not begin Day 3 automatically. At the next session:

1. Read this log, inspect Git state/remote, and run offline tests. Ensure the local
   runner image matches current source; rebuild and run explicit Docker checks.
2. Implement bounded structured model responses/retries and provider usage logs.
   Keep paid adapters disabled until an explicit acceptable spending cap exists.
3. Implement direct repair A using the constrained candidate path, with malformed
   response/forbidden target checks; do not expose evaluator data or filesystem tools.
4. Add resumable batch JSON/JSONL logs that do not silently duplicate completed runs.
   Preserve distinct mock, sandbox-smoke, pilot, and measured run kinds.
5. Validate offline end-to-end operation; run a live pilot only if separately
   authorized and budgeted with verified pricing and conservative accounting.

PowerShell commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
docker build --tag vericode-runner:day2 sandbox
.\.venv\Scripts\python.exe -m vericode sandbox-info
.\.venv\Scripts\python.exe -m vericode run-tests --task clamp --candidate mock --backend docker
.\.venv\Scripts\python.exe -m pytest --run-docker -q
```

Understanding checks: Why must a timeout stop the whole container? Why can visible
test success coexist with a remaining bug? What does a mock patch passing real
tests establish about the model's repair ability?

## 2026-10-12 — Day 3

Inspection: clean `master`, no new `AGENTS.md`, verified GitHub remote/default
branch unchanged. Final Day 2 commit `c039c2d` matches GitHub. Existing offline
checks passed: 87 tests, 17 opt-in Docker checks skipped. Docker Desktop was
stopped; it was started in the background and the trusted image rebuilt from the
unchanged checked-in harness before explicit container checks.

### Task 1 — Structured providers, retries, and usage

- Added provider-neutral request/response/limit/usage contracts and a bounded
  completion wrapper. The mock provider now produces JSON through that wrapper.
- Only transient transport errors retry, with an unchanged prompt. Invalid
  answers stop immediately. Every call contributes usage, including known charges
  from failed calls; unknown totals stay null and known subtotals are separate.
- Paid/network transports are rejected before calls. No live SDK, credentials,
  pricing, or dollar-budget enforcement is configured. Adapter timeouts are an
  explicit contract; see `docs/providers.md` for their limits.
- Checks: offline suite 106 passed, 17 Docker checks skipped. The full Docker-enabled
  suite also passed all 123 checks. Tests cover retry exhaustion, usage retention,
  missing usage, malformed/oversized replies, forbidden targets, input limits,
  disabled paid execution, and secret-bearing exception sanitisation.
- Commit `c8bfdc7` pushed to `origin/master`; remote SHA verified.

### Task 2 — Direct repair A

- Added recorded configuration and a one-response strategy with constrained patch
  validation. Visible execution occurs only after the model response and never
  returns feedback. Invalid responses, invalid patches, visible failures, and
  execution errors have distinct statuses. Unchanged proposals are recorded.
- Added `repair` CLI with configurable model label/call/token limits, mock default,
  explicit Docker selection, and JSON output. Candidate and usage are retained
  if execution fails; evaluator input is never loaded.
- Checks: offline 116 passed, 18 Docker checks skipped; targeted strategy tests
  11 passed with Docker enabled. The first live check returned an infrastructure
  error; the saved CLI check passed, and the diagnostic rerun passed. No test was
  excluded or converted into a passing candidate outcome.
- Saved `artifacts/day3-direct-clamp.json`: one scripted call/response, 2 visible
  test passes, cleanup confirmed, zero API spend, and evaluation unknown. This is
  a local sandbox demonstration, not a live-model repair result.
- Commit `64ef64f` pushed to `origin/master`; remote SHA verified.

### Task 3 — Fixed resumable batches

- Added versioned offline configuration, fixed-manifest batch CLI, runtime/task
  fingerprints, frozen Docker images, directory locks, and bounded append-only
  JSONL start/outcome records. Starts and outcomes are flushed/fsynced; completed
  failures remain outcomes and are not regenerated on resume.
- Changed configuration/task/runtime, torn/corrupt/duplicate events, uncertain
  started calls, and unconfirmed cleanup block automatic replay. Storage capacity
  is reserved before sending a call. Infrastructure failures halt the batch while
  preserving the completed failure; remaining unstarted tasks can resume later.
- Offline checks: 134 passed, 19 Docker checks skipped. An initial combined run
  passed 152 checks but its first Docker batch task reported infrastructure failure.
  The diagnostic batch rerun passed all three tasks and confirmed cleanup. Final
  combined rerun passed all 153 checks, including 19 Docker checks; no case was
  excluded or re-labelled. Saved XML confirms zero failures/errors/skips. Dependency,
  whitespace, and secret-pattern checks passed.
- `artifacts/day3-final-offline-batch` saved three scripted outcomes/calls; resume
  added zero calls and skipped all three. API cost is known zero; token counts and
  evaluation success remain unknown. Earlier development checkpoint snapshots are
  retained; their old runtime/format fingerprints can legitimately reject resume.
- Local engineering report: `artifacts/day3-final-checks.xml` (ignored). No paid
  adapter, funding cap, live pilot, or measured model-performance experiment exists.
- Cleanup verified for all generated `vericode-job-*` containers. An existing
  stopped container outside that namespace was preserved because ownership was
  not established.
- This work session started on 2026-10-12 and crossed into 2026-10-13 in
  Asia/Karachi. Day 3 is a work-session label, not a scheduled automation.
- Task 3 commit: `feat: add durable resumable direct-repair batches`; final hash
  and push verification are reported at session close. Use `git log --oneline -3`
  for Day 3's commits; a commit cannot include its own final hash.

### Day 3 completion and Day 4 starting point

All three Day 3 acceptance criteria are implemented. The provider, direct strategy,
and batch workflow operate offline; explicit Docker runs only visible tests. No
evaluator assets are loaded by these repair paths. No paid API call or release tag
was made. Measured LLM performance remains absent, and containers/checkpoints have
the documented security, crash, and reproducibility limitations.

Stop here; do not begin Day 4 automatically. At the next session:

1. Read this log and inspect Git state/remotes, then run existing offline checks.
2. Implement strategy B with bounded repair-visible feedback/retries using the
   same provider, usage ledger, candidate validation, and isolated executor.
3. Stop on visible success, identical proposals, exhausted attempts/calls, and
   unrecoverable errors. Keep transport retries distinct from repair revisions.
4. Add deterministic mock checks for successful revision, exhausted budgets,
   malformed patches, and absence of evaluator information from model context.
5. Extend recorded configuration and batch formats deliberately; preserve existing
   Day 3 checkpoints rather than silently changing their experiment identity.

PowerShell commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m vericode repair --task clamp
.\.venv\Scripts\python.exe -m vericode batch --run-dir artifacts/my-direct-batch
.\.venv\Scripts\python.exe -m vericode batch --run-dir artifacts/my-direct-batch --resume
.\.venv\Scripts\python.exe -m pytest --run-docker -q
```

Understanding checks: Why can one repair response involve multiple transport
calls? Why is a completed failed patch skipped on resume? Why should a started
task without an outcome remain uncertain instead of being automatically replayed?

## Day 4 — 2026-10-14 (Asia/Karachi)

### Task 1 — Bounded feedback-guided core

- Inspected the clean default branch, verified the user-supplied GitHub remote,
  and passed the existing 134 offline checks (19 Docker checks opt-in).
- Added strategy B: initial visible observation, latest-source revisions, bounded
  feedback projection, typed history, and global call accounting. Per-response
  transport retry limits are clipped to the remaining shared call budget.
- Only repair-visible contents enter requests; controller details/identities and
  runner protocol frames are excluded. Mock execution remains not_executed and
  stops after one response with unknown acceptance. Paid providers stay disabled.
- Checks: 137 offline checks passed, 19 Docker checks skipped; whitespace review
  passed. No candidate or test text executed on the host. Docker Desktop was
  started in the background for subsequent integration verification.
- Task 1 commit: `feat: implement bounded feedback-guided repair`; hash and push
  verification reported after committing. Next: repeated-patch stopping and
  recorded CLI/batch integration, then the complete stopping/isolation test matrix.

### Task 2 — Stops and recorded workflows

- Task 1 committed/pushed as `f171646715645b4091607e1c85703bf93eae5f35`,
  verified against the remote branch.
- Added exact repeated-source/cycle detection before duplicate execution. Initial
  visible success returns unchanged with zero calls. Fatal errors/unconfirmed
  cleanup, malformed replies/patches, and exhausted attempts/calls stop explicitly.
- Added `feedback` CLI and versioned B configuration/records, initial observations,
  full request/candidate/execution history, and resumable B batches. Direct schema 1
  remains intact; B uses schema 2, journal envelope 1. Raised bounded journal line
  capacity to 16 MiB for up to ten bounded histories; total journal stays 64 MiB.
- Checks: 146 offline checks passed, 19 Docker checks skipped. Docker CLI smoke:
  original clamp failed, one scripted response passed both visible tests, cleanup
  confirmed, one mock call, API cost zero, tokens unknown, evaluation null. Artifact:
  `artifacts/day4-feedback-clamp.json` (ignored). No live-model result is implied.
- Task 2 commit: `feat: record feedback repair stopping and resumable workflows`.
  Next: exhaustive deterministic stopping/accounting/isolation cases and final
  Docker integrations. No Day 5 work started.

### Task 3 — Deterministic revision, stopping, and isolation checks

- Task 2 committed/pushed as `fd93b0d26452d8f96b96b1a144b13dd128910095`,
  verified against the remote branch.
- Added deterministic checks for revision success, last-call success, exhausted
  attempts/calls, transient retry clipping, repeated originals/cycles, malformed
  JSON/targets/AST/task IDs, retained last checked candidates, candidate resource
  failures, sanitized adapter exceptions, and unconfirmed cleanup overriding passes.
- Verified the exact request/feedback allowlist excludes controller/evaluator
  sentinels; a repair run needs no evaluation tree. Mock acceptance stays unknown,
  and environment credentials/spending caps cannot enable paid execution. B's
  uncertain checkpoints and initial cleanup failures block automatic pending work.
- A ten-attempt large-history check exceeds the former 2 MiB limit, fits the new
  reserved 16 MiB record, and round-trips all usage/history without dropping entries.
- Initial targeted Docker run passed the repair but failed one assertion expecting
  `AssertionError` in pytest's short output. Corrected the assertion using observed
  failure text. Also removed random XML report announcements and normalized the
  harness-root test label from model feedback; original execution logs remain full.
  The targeted rerun passed 19 checks, including three new Docker integrations.
- Final checks: 185 passed/22 opt-in skips offline; all 207 passed with Docker in
  80.14 seconds, no failures/errors/skips. Report: `artifacts/day4-final-checks.xml`
  (ignored). Dependency consistency, whitespace, and secret-pattern reviews passed.
- Verified no `vericode-job-*` containers remain; unrelated containers were preserved.
- Final CLI smoke: original clamp failed, one scripted patch passed two visible
  tests, cleanup confirmed, cost zero, tokens unknown, evaluation null. Saved as
  `artifacts/day4-final-feedback-clamp.json`. Earlier smoke artifact is preserved.
- `artifacts/day4-final-offline-batch` recorded three mock candidates/calls, cost
  zero, unknown tokens/evaluation; resume skipped three, newly completed zero.
  Docker batch integration used one call: the other two originals already passed
  their weak visible suites. This is engineering evidence, not model performance.
- Task 3 commit: `test: verify feedback stopping accounting and isolation`; final
  hash/push verification reported at session close. Use `git log --oneline -3` for
  the three Day 4 commits; a commit cannot include its own hash.

### Day 4 completion and Day 5 starting point

All Day 4 tasks are complete. A/B share structured providers, constrained patches,
isolated execution, usage accounting, and durable fixed-manifest batches. B records
bounded repair-visible feedback and stopping decisions. No evaluator data entered
the repair workflow, no paid call was made, and no release tag was created. Real
LLM performance and independent evaluation remain absent.

Stop here; do not begin Day 5 automatically. At the next session:

1. Read this log, inspect Git/remotes, and run existing offline checks.
2. Implement C with generated-test validation and independently justified expected
   outputs/properties. Record/discard invalid generated tests; model agreement alone
   is insufficient. Preserve repair/evaluator separation when using a trusted oracle.
3. Inspect original QuixBugs licensing, attribution, references, and test behaviour;
   pin suitable content before importing. Record inconsistencies/exclusions and
   freeze disjoint development/final manifests. No external benchmark is imported yet.
4. Implement independent scoring in isolation after repair, without returning its
   tests, paths, references, or feedback to the agent. Verify a deliberately overfitted
   visible-pass candidate fails the independent suite and is scored accordingly.
5. Commit/push each coherent Day 5 task, document actual evidence/limitations, and stop.

PowerShell commands from the repository root (start Docker Desktop's Linux engine
before Docker commands; choose unused artifact paths for a new run):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m vericode feedback --task clamp
docker build --tag vericode-runner:day2 sandbox
.\.venv\Scripts\python.exe -m vericode feedback --task clamp --backend docker
.\.venv\Scripts\python.exe -m vericode batch --config configs/offline_feedback.json --run-dir artifacts/my-feedback-batch
.\.venv\Scripts\python.exe -m vericode batch --config configs/offline_feedback.json --run-dir artifacts/my-feedback-batch --resume
.\.venv\Scripts\python.exe -m pytest --run-docker -q
```

Understanding checks: Why can one repair attempt consume several transport calls?
Why can B accept an unchanged buggy original with zero calls? Why must evaluator
feedback remain unavailable to the repair loop, even after visible success?
