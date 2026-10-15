# Day 6 pipeline evidence

These are **sandbox demonstrations with mock providers**, not LLM performance
measurements. All repair requests completed before independent evaluator suites
opened. The actual frozen collector is commit
`c484bdbee5914e1f02f3b74020c9248b4b3774af`; protocols record its exact runtime,
dataset/configuration identities and immutable Docker image.

The [development pilot](evidence/development/protocol.json) used scripted repairs:
A/B/C recorded 3/1/6 mock transport calls and 3/1/3 independent-suite passes. B's two
unchanged visible-pass originals failed evaluation. No method-effect claim follows
from these canned examples. After prompt/usage/outcome/cleanup review, a separate
[final protocol](evidence/final/protocol.json) froze the pinned three-task subset.

The final mock emits unchanged source. A/B/C recorded 3/0/6 calls and zero observed
evaluation passes. A and B each had two known failures and one candidate timeout;
C had three unsubmitted patches after repeated-original stopping. Those outcomes
remain unresolved, not silently converted into ordinary failures or successes.
Regression rates are unavailable because no observed original passed its entire
independent suite. Every logged execution confirmed cleanup; no study job remains.

All 19 mock calls have known zero API cost. Total input/output tokens are unknown
(the zero-call final B run consumed none). Docker compute/electricity is not priced.
No paid spending is authorized or performed. See [measurement status](measurement_status.json).

Each evidence directory includes the exact protocol, immutable checkpoint metadata,
complete JSONL start/outcome journal, collection summary and byte-hash manifest.
Scores link to the exact repair payload hash; no full logs were removed. Resume
checks added zero calls and preserved the journal bytes. Git attributes preserve
these bytes across platforms. Source artifacts remain under ignored
`artifacts/day6/`; the reviewed evidence copies are intentionally versioned for
traceability. Checksums are not authenticated provenance.

The [generated analysis](analysis/report.md), [task rows](analysis/tasks.csv),
[method summaries](analysis/summary.csv), [metric JSON](analysis/analysis.json),
[SVG](analysis/outcomes-and-calls.svg) and [PNG](analysis/outcomes-and-calls.png)
are derived from these journals, with exact event/hash links. The
small public, inspected subset, scripted development answers, unchanged final
mocks and lack of live token/cost measurements prohibit LLM or generalisation claims.
