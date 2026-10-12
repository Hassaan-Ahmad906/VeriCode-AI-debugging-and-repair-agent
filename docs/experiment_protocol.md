# Experiment protocol — draft, not frozen

Question: how much do execution feedback and additional test generation improve
LLM-based program repair, relative to their cost?

- A: one direct repair response, without execution feedback. Implemented using
  scripted mocks on Day 3; post-response visible checks do not cause revisions.
- B: repair-visible execution feedback and bounded retries.
- C: independently validated additional tests plus B's feedback loop.

Record actual model calls, attempts, input/output tokens when supplied, latency,
and known cost. A shared budget ceiling is not compute matching. Missing token or
price information remains unknown, never an invented estimate or zero. Paid API
execution is disabled until the user explicitly configures an acceptable budget.

`self-authored-v1` has three development tasks and zero final tasks. Available and
evaluation-only tests are distinct within each task; this is separate from the
development/final task split. The final manifest and full protocol must be frozen
before final measurement. QuixBugs suitability, license, source pin, attribution,
and reference/test consistency are Day 5 work; no content is imported yet.

Score final candidates on evaluation tests unavailable during repair. Report
evaluation-suite success, regressions, accepted-but-failing patches, invalid
patches, timeouts, and infrastructure failures separately. Measure baseline
behaviour before defining a regression. Model-generated expectations require an
independent reference or defensible property; record discarded invalid tests.

Save configurations, task lists, prompts, model identifiers, dataset version,
Git SHA, execution limits, and available seeds. Hosted models may remain
nondeterministic. Day 1 schema tests and mock demonstrations are engineering
checks, not repair-performance results. No measured results exist yet.
