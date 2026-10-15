# Traceable analysis without invented model results

The [Day 6 report](../reports/day6/analysis/report.md) contains task/summary CSVs,
full metric JSON, failure cases linked to completed JSONL events, and standalone
SVG/PNG figures. The source journals and byte-check manifests are versioned next
to it. They contain no live-model experiment. The separate measurement-status
record explicitly states why paid/measured work is absent.

Recreate the historical analysis in a new directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,analysis]"
.\.venv\Scripts\python.exe -m vericode analyze --run-dir reports/day6/evidence/development --run-dir reports/day6/evidence/final --output artifacts/new-analysis --plot
```

Omit `--plot` to generate tables/JSON/Markdown using only the standard library.
Plotting is optional and pinned to [Matplotlib 3.10.8](https://pypi.org/project/matplotlib/3.10.8/).
The exported metadata records actual plotting dependency versions, analysis source
and runtime hashes, source protocols and Git revisions. This is an environment
snapshot, not a universal transitive dependency lock. The image identity remains
part of collection evidence; plots require no Docker or provider access.

Each task row includes actual mock calls, generation calls, repair attempts,
supplied tokens and known subtotals, API cost, local controller latency, observed
suite outcomes, regression/acceptance indicators, exact repair/score hashes,
journal hash, and completed-event line numbers. The reader validates all archive
checksums and repair/score links, and recomputes usage from the call ledger.
Duplicate protocol snapshots reject rather than doubling counts. Existing output
directories are preserved. Studies/protocols/splits stay separate in summaries.

Missing scores and unsubmitted patches remain in the expected task denominator.
Timeouts, infrastructure errors and test errors stay unresolved; observed test
failures stay failures. Unknown token/cost totals remain unknown. Zero-call runs
have zero token usage; a known subtotal is not a complete measurement. Regression
rates require baseline suite passes with known candidate outcomes; suite-level
metrics do not detect every per-test regression when the baseline already fails.
Missing-outcome bounds are not confidence intervals. Local timing/API cost columns
do not price Docker compute or measure hosted-model speed.

The development pilot uses canned fixes, so it cannot estimate model ability or
an A/B/C effect. The final no-op mock reveals ordinary test failures, bounded
timeouts and unsubmitted patches rather than a repair gain. The three public,
inspected final tasks are selected/adapted, not a blind or representative benchmark.
No novelty, significance, generalisation or internship outcome is claimed.

Historical evidence may be analysed under later code because original source
identities remain recorded. Collection resume deliberately rejects changed runtime:
freeze a new protocol/run directory for another collection under current code.
Do not edit old fingerprints or regenerate failed outcomes to make a run resume.
