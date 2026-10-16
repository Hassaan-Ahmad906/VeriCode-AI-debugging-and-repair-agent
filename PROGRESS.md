# Progress

## 2026-10-16 — Dark workspace, user-owned APIs and deployment preparation

- Rebuilt the interface around a focused Overview and separate Repair, Runs,
  Models & API, Usage & cost, Training, Deployment and Research pages. Dark theme,
  desktop/mobile browser review, no configuration or editor on the home page.
  Real repair defaults to local Ollama, Docker, feedback and the failing clamp
  fixture; simulation remains an explicit option.
- Enabled per-session OpenAI/OpenRouter keys: metadata verification, live official
  model/pricing discovery, model selection, positive spending cap, explicit
  authorization and connection. Disconnect forgets the key. No key enters run
  records, global environment or candidate containers. Context-local connection
  isolation and an SQLite per-key ledger prevent shared-session credentials,
  concurrent reservations and refunds of unknown billing outcomes.
- OpenAI USD amounts are fetched-standard-rate estimates; OpenRouter uses its
  response's USD cost. Unknown usage remains unknown. Pricing freshness, route
  price caps, conservative reservations and no paid automatic retries are
  enforced. Public OpenAI pricing (40 rows) and OpenRouter catalog (466 models)
  fetched successfully with the actual HTTPS adapter. No real key or paid call
  was used during development; live account/model compatibility remains an owner
  connection check. Historical scripted study/batch protocols remain unchanged.
- Prepared `deploy/bootstrap.sh`, systemd unit and private Linux VM/SSH guide.
  Bash syntax passed; Linux deployment is not runtime-verified. Hosting is not
  selected or published. This remains a private workspace, not public SaaS.
- Final full regression run: 289 passed including 27 Docker checks. After minor
  UI default refinements, 33 targeted checks passed, with one explicit Docker
  skip. The first full run correctly rejected edits made during a frozen study;
  a stable retry passed, then the final stable full suite passed. Dependency
  consistency, whitespace review and browser page navigation passed.
- New real dark-UI/local-model development check: clamp, B feedback, one call,
  487 input / 65 output tokens, $0 API, visible and independent suites passed.
  Local raw record retained at `artifacts/dark-ui-live.json`. This is a repeated
  development smoke check, not a controlled method comparison. No historical
  Day 6/7 evidence bytes were changed.
- Owner reports Colab GPU detected and cells running. Completed adapter, training
  losses and GGUF have not been received or verified. Keep the runtime open,
  download the adapter ZIP (manifest inside) and optional GGUF/export JSON/license;
  then inspect actual provenance and independently compare base versus adapter.
- Remaining owner actions: enter personal provider keys/limits in the UI; finish
  Colab and provide its artifacts; choose a host later. No cloud fees were incurred
  by this implementation. Local app/model services remain running on request.
- Commit: `feat: add dark workspace and budgeted user-owned model connections`;
  exact push/CI outcome is verified after committing rather than assumed here.

## 2026-10-16 — Day 7 task 3: local prototype delivery

- Workspace/model commit pushed and verified: `e170ada6cc1a86ec5ece19c3d97d1a7e7dc9b4fd`.
- Completed attribution, fresh setup/release criteria, two-minute demo and offline
  CI for Python 3.11/3.13; official v7 actions pinned to verified commit hashes.
- Full suite: 273 passed including 27 Docker checks. Fresh editable environment:
  246 offline passed, 27 explicit Docker skips; dependency consistency passed.
  Final schema/UI refinements passed 15 targeted checks. Real UI/model/Docker
  repair passed 2 visible and 3 independent tests; all failed trials retained.
- Built/installed wheel in a separate environment without dependencies/network;
  task listing/mock demo passed. All workspace/model modules are packaged.
  Evidence checksums and secret-pattern review passed; no VeriCode jobs remain.
- Local UI and free model server remain running because the user requested them.
  Visually reviewed desktop/models/training/history/research/mobile screens;
  refined responsive metrics and mobile navigation. Final packaging/CI/tag
  verification follows this commit; remote CI is not assumed to have passed.
- Required from owner: sign in to Colab, choose an available free GPU and run the
  smoke/full training/export notebook. No cloud training, custom trained weights
  or measured fine-tuning improvement is claimed. Hosted paid APIs stay disabled.
- Next session: verify Git/remotes, inspect actual Colab manifest/adapter if
  produced, validate the export, then freeze a base-versus-adapter comparison.
- Start UI: `.\.venv\Scripts\python.exe -m vericode.ui_launcher`; localhost:8501.
  Start model after reboot: `powershell -File scripts/start-local-model.ps1`.
  For real AI select Local Ollama, B feedback and Docker in the workbench.
- Understanding checks: Why does a response schema not prove correctness? Why
  does lower training loss not prove better repairs? Why retain failed trials?
- Commit: `chore: finish local prototype release workflow`; final hash and any
  verified tag are reported after push. A commit cannot contain its own hash.

## 2026-10-16 — Professional workspace and real free model

- Training workflow pushed and verified:
  `546f5407971215eab2d983e42cd8cd3a11cc191d`.
- Replaced the basic UI with a full local workspace: dark navigation, workbench,
  code/spec/test tabs, diff/source/results/attempts, real session counters, recent
  history, model settings, training studio and research evidence. Retains custom
  inputs/configuration through navigation; responsive metrics and local theme.
  This is a local single-user application, not an authenticated enterprise service.
- Applied Sites skill's local-only guidance; no Site registration, sync, public
  hosting or deployment. Visually inspected desktop workbench/models/training and
  mobile rendering through a separate owned Edge session. Seven UI checks pass.
- Downloaded official Ollama 0.40.5 portable CPU runtime, resumed the interrupted
  download with strict byte-range validation, and verified full official SHA-256.
  Installed qwen2.5-coder:1.5b, CPU-only, loopback-only, OLLAMA_NO_CLOUD=1, one model
  and one request at a time. Runtime/weights remain ignored in artifacts.
- Added local provider factory integration for A/B/C, real reported token usage,
  bounded native HTTP with no proxies/redirects, cloud alias rejection, strict
  response schemas, context/output allowance and safe failures. Hosted API fields
  are disabled under the user's free-only choice; no credential is needed or saved.
- Local attempts: JSON-only malformed A rejected; schema A kept a buggy original;
  feedback B produced a changed patch, passed 2 visible/3 independent checks;
  the redesigned UI independently ran B and passed both suites too. Four actual
  local calls total, 1470 input/367 output tokens, $0 API cost. All trials retained
  in reports/day7 with hashes, failures, model manifest and provenance limitations.
  This single development fixture is not a controlled A/B effect measurement.
- Checks: 273 full checks passed including 27 Docker tests; fresh virtual
  environment passed 246 offline with 27 explicit Docker skips. Final schema/UI
  refinements passed all 15 targeted checks; all 246 offline re-passed after the
  local schema change. Actual redesigned UI + local model + Docker + independent
  evaluator also passed, separate from the automated offline suite.
- Concept: a structured response schema constrains answer shape, not correctness.
  The independently observed failure and later feedback success remain distinct.
- Next: final packaging/CI/setup checks, refresh live UI, commit/push and tag only
  if local prototype criteria pass. Commit: `feat: build professional local repair workspace`.

## 2026-10-16 — Free cloud customization extension

- User chose free-only local inference and free cloud training preparation; no
  paid API/cloud budget is authorized. Added a Colab notebook with an explicit
  CUDA preflight, pinned training dependencies, immutable base revision, two-step
  smoke run, rank-8 4-bit LoRA, maximum three epochs and early stopping.
- Added 120 self-authored training and 24 validation examples, split by operation
  family; no benchmark/reference/evaluator reads. Prompt loss masking and context
  rejection have coverage. All 12 authored target families passed in Docker.
- Optional export merges the exact base, preserves its license and uses pinned
  llama.cpp conversion/quantization plus a model checksum. Adapter and export
  recipes are not GPU-runtime verified here; no trained model or improved repair
  quality is claimed. User must sign in and start a free Colab GPU runtime.
- Checks: three offline dataset/masking/notebook checks passed; target-example
  Docker validation passed as part of all 272 system checks. Notebook has no
  fabricated outputs. Training/merge scripts parse without importing GPU packages.
- Report pushed/verified: `b727036daded8a2d50423b778186425d4f75faf0`.
- User rejected the initial UI's visual quality. A professional workspace redesign
  is in progress; navigation/persistence/history checks now pass (7 UI checks).
- Runtime download timed out near 1.2 GB; added strict byte-range resume and kept
  the partial download. Full SHA-256 is required before extraction/execution.
- Next: visually verify workspace, finish real local-model smoke, release checks.
  Commit: `feat: prepare free GPU adapter training and export`.

## 2026-10-16 — Day 7 task 2: evidence-based report

- Task 1 UI pushed and remote hash verified:
  `76a32267feaf26c1de3924f6f111f4818991244d`.
- Added `reports/research_report.md`: question, A/B/C methods, execution/data
  boundaries, six rows from the frozen Day 6 analysis, failure interpretation,
  actual 19 mock calls/$0 API, missing live measurements and primary related work.
- Explicitly distinguished the new local-model/LoRA extension from historical
  scripted evidence. No cloud training or fine-tuning improvement is claimed.
- Review: table reconciled with `reports/day6/analysis/summary.csv`; checked
  original papers/model/API documentation. Earlier adapter refactoring required
  updating a provider-injection test to its new factory; that targeted suite now
  passes. Full Docker verification is in progress alongside the runtime download.
- Concept: independent tests can reject agent-accepted code; visible success,
  training loss and independent correctness are different observations.
- Next: finish free local runtime/model, customization notebook, release CI/setup
  and final verification. Commit: `docs: report methods and scripted evidence`.

## 2026-10-16 — Day 7 task 1: local interface

- User authorized completing the system. Added an optional pinned Streamlit UI,
  loopback-only launcher, source/diff/history/usage views, JSON downloads and a
  separate independent-evaluation action using the existing CLI controllers.
- Configuration changes discard stale results; unconfirmed cleanup blocks jobs.
  No candidate/test execution on the host. Mock remains the default.
- Checks: existing baseline 228 passed with 26 Docker opt-in skips; five new
  Streamlit AppTest/launcher checks passed, including evaluator separation,
  stale-result invalidation and cleanup blocking. Streamlit 1.64.0 installed.
- User expanded scope to local models, API settings and model customization,
  then chose free-only operation and approved the local runtime/model download.
  No paid API or cloud spending is authorized. Laptop: i7-1355U, about 16 GB RAM,
  Intel Iris Xe; no NVIDIA GPU. Prepare a free-GPU LoRA workflow, not a claim of
  training a competitive coding language model from scratch on this laptop.
- Next: finish local inference integration/setup; prepare customization workflow;
  complete report, CI, fresh-install verification, demo and release checks.
- Commit: `feat: add local Streamlit repair interface`; hash reported after push.

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

## Days 5 and 6 — 2026-10-15 (Asia/Karachi)

The user explicitly authorized both work sessions today. Complete Day 5 and Day 6,
then stop before Day 7. Paid API execution remains disabled.

### Day 5 task 1 — Independently checked generated tests

- Inspected the clean repository and verified origin/master at `d5b66b8`; baseline
  185 offline checks passed, 22 Docker checks opt-in. Started Docker Desktop hidden.
- Added C with bounded JSON case generation, versioned specification rules,
  literal rendering, discard reasons, shared generation/repair call accounting,
  purpose-labeled calls, schema 3 configuration, CLI and batch dispatch.
- No arbitrary model test code executes on the host. Wrong expectations, duplicate
  cases, unsupported domains, malformed envelopes and test-name collisions are
  rejected. Original visible tests remain intact; evaluator inputs are absent.
- Checks: 196 offline passed, 23 Docker opt-in skips; targeted C suite passed all
  12 checks including Docker. Generated negative input exposed the weak positive-sum
  visible suite; scripted repair passed all three augmented tests. No paid calls.
- Commit: `feat: add independently validated test-augmented repair`; next inspect
  pinned benchmark licensing/reference behaviour, adapt a documented subset, and
  freeze disjoint task manifests.

### Day 5 task 2 — Pinned benchmark and frozen splits

- Task 1 pushed/verified: `af13ee0d36b5c8a9fa55e05041851cb9401ede90`.
- Reviewed QuixBugs revision `4257f44b0ff1181dedaedee6a447e133219fcebf`,
  MIT notice/legal notes, selected buggy/reference programs, JSON/pytest tests,
  loader and driver. Preserved license and vendored bytes; provenance enumerates
  all 47 other Python-program files as outside this deliberately small audit.
- Adapted three standalone final tasks without editing buggy source. One upstream
  case per task is visible; remaining cases are evaluator-only. Added one documented
  empty-search edge case and explicit gcd(0,0) convention. All 16 upstream expected
  values agree with independent specification rules. No case silently fixed/dropped.
- Docker audit: all three references passed all 17 adapted cases; original gcd
  and parentheses failed, binary search timed out on an absent low value. All six
  jobs confirmed cleanup. Preserved timeout/unknown counts. Compact summary and
  source hashes are versioned; full artifact `artifacts/day5-quixbugs-audit.json`.
- Froze disjoint development/final manifests and canonical repair fingerprints;
  evaluation fingerprints are separate. Frozen repair verification needs no
  evaluation tree. Final mocks explicitly propose unchanged source, not references.
- Checks: 199 offline passed, 23 Docker opt-in skips; source-byte/oracle/freeze
  tests passed. This is an adapted three-task audit, not full-benchmark coverage,
  blind validation, or a measured model result.
- Preserved an upstream trailing blank line in the reference gcd file; a narrow
  whitespace attribute exempts only its blank-at-EOF warning. Byte hashes verify
  all vendored content; project-authored whitespace checks remain enabled.
- Commit: `feat: add pinned QuixBugs subset and frozen data splits`; next independent
  post-repair scoring, regression metrics and an overfit rejection check.

### Day 5 task 3 — Independent evaluator and metrics

- Task 2 pushed/verified: `84cfe40c864b8261512f0eef13ac72c3bb522b90`.
- Added post-repair scoring with task/configuration/source/suite validation,
  original baseline and final-candidate observations, immutable repair artifacts,
  separate evaluation records, no provider calls and no feedback into repair.
- Added regression and accepted-but-failing metrics with explicit denominators,
  unknown outcomes, execution-status counts and missing-outcome bounds. Missing/
  rejected candidates are not executed or credited. Cleanup failure stops jobs.
- Saved-record parsing is bounded to 16 MiB, accepts real attempt-history sizes,
  and rejects duplicate/non-finite JSON. Small dataset/config readers stay bounded.
- Acceptance: the unchanged positive-sum program passes visible tests with zero
  B calls, then fails independent evaluation; a scripted clamp repair passes.
  Original failures remain distinct from regressions and unresolved executions.
- Checks: all 236 passed in 89.46 seconds, including 25 Docker checks; XML confirms
  zero failures/errors/skips (`artifacts/day5-final-checks.xml`, ignored). Dependency,
  whitespace and secret-pattern checks passed. No candidate/test host execution.
- Commit: `feat: add independent scoring and regression metrics`.

### Day 5 completion

All three tasks are complete. Commands and boundaries are documented in
`docs/generated_tests.md`, `docs/benchmark.md` and `docs/evaluation.md`. Paid
execution remains disabled. Engineering checks/reference audits do not measure
LLM performance. The final subset is public, small, adapted and inspected.

```powershell
.\.venv\Scripts\python.exe -m vericode augment --task sum_positive --backend docker --output artifacts/new-repair.json
.\.venv\Scripts\python.exe -m vericode evaluate --record artifacts/new-repair.json --backend docker --output artifacts/new-score.json
```

Understanding checks: Why reject an expected value that matches buggy code?
What distinguishes a regression from an already-failing original? Why does a
timeout leave the evaluation-suite outcome unknown?

Continue to Day 6 today under the user's explicit two-session authorization:
freeze actual configurations/identities before collection, verify conservative
resumption and accounting, run only offline/sandbox demonstrations, then produce
traceable analysis and explicitly record missing live-model results. Stop before
Day 7; no paid model adapter or live spending is authorized.

### Day 6 task 1 — Frozen two-phase study collection

- Day 5 task 3 pushed/verified: `61ce1593d73ff0c105db43427589d0fb6febdbd8`.
- Added strict zero-cost study configuration, immutable pre-collection protocol
  snapshots, exact task/configuration/runtime/prompt/oracle identities and frozen
  Docker image IDs. Same per-response limits, model and execution controls are
  required across methods; actual calls/tokens remain distinct, not compute-matched.
- Added durable A/B/C collection with all repairs before independent scoring,
  per-phase/task started/outcome envelopes, conservative resume, error stopping,
  storage reservation, and aggregate usage/unknown-outcome metrics. Live adapters
  and paid caps remain unimplemented; explicit nonzero/paid study configs reject.
- An initial study test caught a Windows default-encoding hash error for the
  existing non-ASCII vowel evaluator case. Fixed importer reads to explicit UTF-8
  and corrected only its frozen hash, not test content. Added a regression check
  over every development/final evaluation-suite fingerprint before any collection.
- Targeted offline protocol/study/benchmark checks passed (13, one Docker opt-in
  skip). Docker study verification and complete offline checks reported below.
- Docker study check passed: development A/B/C collection scored seven passes,
  two failures and two accepted-but-failing cases using ten scripted calls; resume
  added zero calls. Targeted suite passed ten checks. Later exact repair/score-link
  validation passed its targeted checks; full offline suite passed 222, 26 skipped.
- Whitespace and secret-pattern checks passed. These study tests are engineering
  evidence only; persistent pilot/final demonstrations are collected next.
- Commit: `feat: freeze and collect resumable offline studies`; next run and review
  a development pipeline pilot, freeze a separate final demonstration, and retain
  the explicit absence of measured LLM results.

### Day 6 task 2 — Reviewed pilot and final-split demonstration

- Task 1 pushed/verified: `c484bdbee5914e1f02f3b74020c9248b4b3774af`.
- Froze development protocol `a6a00e0e...` before collection; all nine repair
  requests completed before all nine scores. A/B/C used 3/1/6 mock calls and
  passed 3/1/3 independent suites. Two unchanged B originals were accepted but
  failed evaluation. Reviewed prompts, actual usage, outcomes and cleanup first.
- Then froze separate final protocol `e2aca758...`, with the same source/runtime
  and immutable image. No-op final mocks used 3/0/6 calls. Recorded zero observed
  passes, four known failures and five unresolved candidate outcomes (two timeouts,
  three unsubmitted C patches). Retained all cases; no silent retries/exclusions.
- Both studies completed all 18 phase outcomes, resumed with zero new work/calls,
  and confirmed cleanup for every logged job. No `vericode-job-*` remains.
- Archived complete protocols/checkpoints/JSONL journals and byte-hash manifests
  under `reports/day6/evidence`; source artifacts remain ignored. Archive hashes
  and repair/score links were verified. Git attributes preserve exact evidence
  bytes across platforms; no secret patterns found in the reviewed logs.
- Total: 19 mock transport invocations, zero live calls/API dollars. Tokens remain
  unknown except zero-call runs; local compute cost was not priced. Published an
  explicit missing-measurement record. These are sandbox demonstrations, not a
  funded pilot, live-model comparison, or generalisation evidence.
- Commit: `data: preserve reviewed offline study evidence`; next traceable tables,
  standalone plots, failure analysis, final validation and stop before Day 7.

### Day 6 task 3 — Traceable tables, plots and failure analysis

- Task 2 pushed/verified: `174fecacfdcd28040859e07642d50d41ca9de614`.
- Added historical-evidence analysis with byte/repair-score-link validation and
  call-ledger reconciliation, duplicate-protocol rejection, complete expected task
  matrices, separate protocol/split/method groups and explicit missing outcomes.
- Exported 18 task rows, six method summaries and 11 failure cases with exact
  payload hashes, journal hashes and event lines. Unknown tokens remain unknown;
  zero-call runs consumed none. Costs are API-only, not local compute pricing.
- Exported standalone SVG/PNG figures using optional pinned Matplotlib 3.10.8;
  actual plotting dependency versions and analysis source/runtime hashes are saved.
  Visually reviewed the figures and corrected overlapping legend/title placement.
  Core CLI/runtime still has no mandatory third-party dependency.
- Report: `reports/day6/analysis/report.md`; complete CSV/JSON/figures/checksums and
  original evidence are intentionally versioned. Every reported row links to a
  saved event. Verified committed Git evidence bytes, all output hashes, and exact
  final analysis source/runtime fingerprints. No paid or measured LLM results.
- Checks: 228 offline passed, 26 Docker opt-in skips. Final full run passed all
  254 in 151.46 seconds, including 26 Docker checks, zero failures/errors/skips.
  XML: `artifacts/day6-final-checks.xml` (ignored). Six targeted analysis checks,
  dependency consistency, whitespace and secret-pattern reviews passed.
- Final staged lint found trailing path-line spaces emitted by Matplotlib's SVG
  backend. Normalized equivalent SVG whitespace before checksumming, preserved the
  earlier generated report under ignored artifacts, regenerated the report, and
  re-passed all six analysis checks. Repair/execution behaviour was unchanged.
- This authorized two-work-session run began on 2026-10-15 and crossed into
  2026-10-16 in Asia/Karachi. Day labels describe work sessions, not scheduled jobs.
- Commit: `feat: add traceable demonstration analysis and figures`; final hash
  and push verification reported at session close. Use `git log --oneline -6`
  for all six Day 5/6 commits; a commit cannot include its own final hash.

### Days 5 and 6 completion and Day 7 starting point

Both requested work sessions are complete. C independently validates test cases,
the selected benchmark is pinned/attributed/audited, original and final sources can
be scored independently, and A/B/C pipeline studies freeze identities and preserve
complete evidence. Analysis retains known failures, timeouts, unsubmitted patches
and unknown usage. Zero paid calls were made. No live adapter, funded pilot, LLM
effect measurement, public execution service or release tag exists.

Do not start Day 7 automatically. Next session:

1. Read this log and PLAN, inspect Git/remotes and run existing offline checks.
2. Build the local Streamlit UI using the same validated task/configuration,
   repair and isolated execution backends. Display source, patch, visible outcomes,
   attempt history, resource usage and separately labeled independent scores.
   Never execute submitted/generated code or tests on the host; mock is default.
3. Write a concise research/portfolio report grounded in the Day 6 evidence.
   Separate scripted engineering observations from absent measured LLM results;
   explain test coverage, public/inspected subset selection, small samples, unknown
   token/cost information, suite-level regressions and container limits.
4. Polish attribution, offline CI, fresh-environment instructions and a two-minute
   local demo. Verify required checks and safeguards before considering a release
   tag. Keep paid execution disabled until explicit funding configuration and a
   conservatively budgeted live adapter exist. Do not infer spending permission.
5. Commit/push each coherent Day 7 task; preserve historical evidence/checkpoints.

Commands from the repository root; start Docker Desktop's Linux engine before
Docker execution and choose unused output paths:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m vericode augment --task sum_positive --backend docker --output artifacts/new-c-repair.json
.\.venv\Scripts\python.exe -m vericode evaluate --record artifacts/new-c-repair.json --backend docker --output artifacts/new-c-score.json
.\.venv\Scripts\python.exe -m vericode study freeze --config configs/study_mock.json --split development --output artifacts/new-protocol.json
.\.venv\Scripts\python.exe -m vericode study run --protocol artifacts/new-protocol.json --run-dir artifacts/new-study
.\.venv\Scripts\python.exe -m vericode analyze --run-dir reports/day6/evidence/development --run-dir reports/day6/evidence/final --output artifacts/new-analysis
.\.venv\Scripts\python.exe -m pip install -e ".[dev,analysis]"
.\.venv\Scripts\python.exe -m vericode analyze --run-dir reports/day6/evidence/development --run-dir reports/day6/evidence/final --output artifacts/new-plotted-analysis --plot
.\.venv\Scripts\python.exe -m pytest --run-docker -q
```

Historical study collection resume rejects the changed analysis/runtime code;
freeze a new protocol to collect again. Read-only analysis intentionally accepts
historical evidence and records original source identities without rerunning calls.

Day 6 understanding checks: Why do actual calls differ despite budget ceilings?
Why retain unresolved outcomes in the task denominator? What can a scripted
demonstration establish, and what still requires a funded live-model experiment?
