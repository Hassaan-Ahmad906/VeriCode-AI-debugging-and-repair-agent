# Seven work sessions

Each day is a work session, not an automation. Complete the current day and stop.
Use plain Python, pytest, a provider-neutral interface, and minimal dependencies.
For each coherent task: check, review, update the log, commit intended files, push
to a verified remote, and verify the push. Never rewrite history or force-push.

## Day 1 — Foundation and executable task format

- [x] Task 1: package, CLI, setup instructions, and plan. Accept when editable
  installation, console entry point, and CLI help work.
- [x] Task 2: task/candidate/execution/evaluation schemas and self-authored
  fixtures, separating repair and evaluation tests. Accept when malformed tasks
  produce useful errors and data boundaries have automated coverage.
- [x] Task 3: mock provider and end-to-end pipeline. Accept when an offline test
  loads a task, obtains a patch, and records an explicitly mock result.

## Day 2 — Isolated execution

- [x] Task 1: implement Docker limits: no network, non-root user, bounded CPU/memory/PIDs/time,
  dropped capabilities, no-new-privileges, read-only root, bounded temporary space.
- [x] Task 2: control workspace, paths, output, full-job timeout termination, and cleanup.
- [x] Task 3: verify completion, exceptions, timeouts, source immutability, and absence of
  credentials, Docker socket, unintended host files, and evaluation assets during
  repair. Document checks that cannot run; never fall back to host execution.

## Day 3 — Direct-repair baseline

- [x] Task 1: add structured provider responses, bounded API retries, and usage accounting.
- [x] Task 2: implement A with constrained patches; reject forbidden paths and invalid output.
- [x] Task 3: add resumable batch logs without silent duplicates. Accept offline end-to-end
  checks. Live pilot requires explicit spending authorization, configuration,
  verified prices, and conservative cost enforcement.

## Day 4 — Feedback-guided repair

- [x] Task 1: implement B with visible-test feedback and bounded attempts.
- [x] Task 2: stop on visible success, repeated patches, budget exhaustion, or fatal errors.
- [x] Task 3: accept deterministic tests for revision, exhausted budget, malformed patches,
  and evaluator-information isolation.

## Day 5 — Additional tests and independent evaluation

- [x] Task 1: implement C with independently justified expected values/properties; log and
  discard invalid generated tests. Model agreement is not independent evidence.
- [x] Task 2: inspect original QuixBugs license, attribution, references, and test behaviour
  before importing anything. Pin a suitable revision; record all inconsistencies
  and exclusions. Freeze disjoint development and final task manifests.
- [x] Task 3: implement independent evaluation and metrics; accept a test showing that an
  overfitted visible-test success fails the evaluation suite.

## Day 6 — Experiments and analysis

- [x] Task 1: freeze protocol/configuration before final runs; record task list, prompts,
  model identifiers, dataset revision, Git commit, limits, and available seeds.
- [x] Task 2: complete a zero-cost pipeline pilot/final demo; no funded live pilot
  was run because no paid adapter or spending authorization exists.
- [x] Task 3: produce traceable tables/plots and failure analysis. Separate measured, pilot,
  demonstration, and mock results. If paid runs are unavailable, finish tooling
  and explicitly report that measured results are absent.

## Day 7 — Demo and portfolio release

- [x] Add a local Streamlit UI sharing CLI backend and execution safeguards.
- [x] Write a concise research report with actual results if available and limitations.
- [x] Polish attribution, offline CI, fresh-install instructions, and two-minute demo.
  Tag a release only after documented release criteria pass.

## Free model customization extension (requested during Day 7)

- [x] Install and verify a free CPU coding model; integrate with CLI/UI and Docker.
- [x] Prepare self-authored data, free-GPU LoRA notebook and laptop export recipe.
- [ ] Owner starts a free Colab GPU session; run training and export, retain actual
  results, then independently compare base and adapted models. No GPU session or
  account access exists in this local environment, so training is not claimed.
