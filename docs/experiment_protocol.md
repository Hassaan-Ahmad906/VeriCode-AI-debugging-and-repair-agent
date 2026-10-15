# Experiment protocol — versioned demonstration procedure

Question: how much do execution feedback and additional test generation improve
LLM-based program repair, relative to their cost?

- A: one direct repair response, without execution feedback. Implemented using
  scripted mocks on Day 3; post-response visible checks do not cause revisions.
- B: repair-visible execution feedback and bounded retries, implemented on Day 4.
  Initial visible success returns unchanged with zero calls. Exact repeated source,
  malformed output/patches, exhausted attempts/calls, and infrastructure failures
  stop. Candidate test errors/time/output/resource limits may inform a revision.
- C: independently validated additional tests plus B's feedback loop.

Record actual model calls, attempts, input/output tokens when supplied, latency,
and known cost. A shared budget ceiling is not compute matching. Missing token or
price information remains unknown, never an invented estimate or zero. Paid API
execution is disabled until the user explicitly configures an acceptable budget.

`self-authored-v1` has three development tasks; the disjoint final manifest now has
three pinned tasks from `quixbugs-4257f44-v1`. Available and
evaluation-only tests are distinct within each task; this is separate from the
development/final task split. The final manifest and full protocol must be frozen
before collection. The selected QuixBugs license, pin, adaptations and reference
audit are documented in `benchmark.md`; this is not the full or a blind benchmark.

Score final candidates on evaluation tests unavailable during repair. Report
evaluation-suite success, regressions, accepted-but-failing patches, invalid
patches, timeouts, and infrastructure failures separately. Measure baseline
behaviour before defining a regression. Model-generated expectations require an
independent reference or defensible property; record discarded invalid tests.

Save configurations, task lists, prompts, model identifiers, dataset version,
Git SHA, execution limits, and available seeds. Day 3 batches additionally save
source/task/configuration fingerprints and append-only start/outcome events.
Resumption preserves terminal failures and blocks uncertain call replay. Hosted models may remain
nondeterministic. Day 1 schema tests and mock demonstrations are engineering
checks, not repair-performance results. No measured results exist yet.

B's default ceiling is three repair attempts, six total transport calls, and three
transport calls per attempt, clipped to remaining calls. Logs retain initial
execution and each request, candidate, execution, and call index. Defaults are
engineering demonstration limits; freeze experimental budgets before final runs.
Mock execution supplies no observed feedback and stops after one candidate with
unknown acceptance. Scripted responses tested inside Docker are sandbox smoke
checks. No A/B effect size or model-performance comparison can be inferred.

Day 6 implements immutable per-run protocol snapshots via `study freeze`, then
durable two-phase A/B/C collection. The supplied mock and Docker configurations
admit only zero-cost scripted/no-op providers. Snapshot identities and actual
prompts/usage preserve each demonstration; they do not establish live-model ability.
Use `studies.md` for pilot/review/final-demo procedures and failure recovery.
Measured, pilot and demonstration labels must not be pooled. No live-model
measurement or funded pilot exists; future paid work requires a new frozen protocol.
