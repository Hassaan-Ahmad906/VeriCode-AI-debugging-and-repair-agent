# Independent post-repair scoring

Save a repair, then independently score it from the repository root:

```powershell
.\.venv\Scripts\python.exe -m vericode feedback --task sum_positive --backend docker --output artifacts/new-repair.json
.\.venv\Scripts\python.exe -m vericode evaluate --record artifacts/new-repair.json --backend docker --output artifacts/new-score.json
```

Choose unused output paths. Without `--backend docker`, scoring remains mock and
all suite outcomes are unknown. Actual candidate/evaluator code runs only in the
constrained Docker runner. Scoring never invokes a provider or mutates the repair
artifact. Its output is not fed back into repair. Experiment runs finish all repair
requests before loading evaluator suites.

The evaluator validates task identity/version/split, source/test fingerprints,
strategy/configuration/schema, and candidate target/AST before opening evaluator
files. Frozen suite fingerprints must match. It checks original and final source
separately on the same evaluation suite; original behaviour defines regressions.
Cleanup/infrastructure failure stops further jobs. Missing candidates remain
unsubmitted; timeouts, collection/test errors and infrastructure are unresolved
suite outcomes, distinct from observed assertion failure.

Records include both executions, source/suite and repair-record hashes, observed
suite success, regression and accepted-but-failing indicators. Metrics retain the
full task denominator, known passes/failures/unknowns, execution-status counts,
baseline-pass and accepted-candidate denominators. A complete pass fraction is
reported only when every suite outcome is known; otherwise lower/upper observed
bounds retain unresolved cases. These are missing-outcome bounds, not statistical
confidence intervals. No empty-suite or mock run counts as a passing evaluation.

The positive-sum fixture demonstrates a visible-pass unchanged program failing
the independent suite. A scripted clamp repair passes both; neither is evidence
of a live model's ability. The evaluator/host remain trusted and public test data
may be contaminated. Finite-suite success is not proof of correctness.
