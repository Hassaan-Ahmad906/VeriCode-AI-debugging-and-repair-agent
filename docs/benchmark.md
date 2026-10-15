# Pinned, adapted QuixBugs subset

Source: [jkoppel/QuixBugs](https://github.com/jkoppel/QuixBugs/tree/4257f44b0ff1181dedaedee6a447e133219fcebf),
revision `4257f44b0ff1181dedaedee6a447e133219fcebf`, reviewed 2026-10-15.
The upstream MIT permission and copyright notice are preserved verbatim in
`data/benchmark/quixbugs/upstream/LICENSE`. Upstream `legal_notes.txt` was also
reviewed; it records historical ownership uncertainty and permission correspondence.
We record its hash/link without reproducing public email addresses. This is a
provenance record, not an independent legal determination. See the pinned
[license](https://github.com/jkoppel/QuixBugs/blob/4257f44b0ff1181dedaedee6a447e133219fcebf/LICENSE)
and [legal notes](https://github.com/jkoppel/QuixBugs/blob/4257f44b0ff1181dedaedee6a447e133219fcebf/legal_notes.txt).

This is a deliberately small **adapted subset**, not the full QuixBugs benchmark.
Before behavioural checks we chose three standalone, bounded-input functions with
reviewable specifications and JSON cases: gcd, find_first_in_sorted, and
is_valid_parenthesization. All other Python-program files (including helpers and
test drivers) are enumerated as out of scope in `provenance.json`; they have not
been judged unsuitable or silently treated as passed. No performance-based task
exclusion occurred. Small-sample and selection bias are substantial.

## Adaptations and findings

- Buggy source is unchanged. Repair target is renamed solution.py; entry-point
  names stay unchanged. Reference source remains evaluator/audit-only.
- One original JSON case per task is repair-visible; every other original case
  is evaluator-only. We render literal pytest assertions instead of upstream's
  dynamic import/--correct driver. Upstream's loader reads one JSON pair per line.
  No upstream assertion, expectation, or case was silently repaired or dropped.
- An additional evaluator case checks an empty search list. The adapted search
  specification explicitly permits it. gcd(0,0)=0 is an explicit convention;
  upstream's informal "greatest divisor" wording alone is ambiguous there.
- All 16 original expected values agree with independent specification rules.
  Corrected reference files passed the 17 adapted cases in Docker. Their alternate
  implementations inside triple-quoted strings are retained as upstream text.
- The buggy gcd failed via recursion; buggy parentheses failed on unmatched opens.
  Buggy binary search timed out on absent values below the minimum. The timeout
  is retained as a timeout, with unknown aggregate test counts, rather than being
  rewritten as an ordinary test failure or excluded.
- The selected tests use no slow-test skips or extra plugins. Upstream documents
  slow/timeout-sensitive tests elsewhere; those programs are outside this subset,
  not audited successes. See the pinned upstream README.

Development remains the three self-authored tasks. Final task IDs are the three
`quix_*` tasks, dataset `quixbugs-4257f44-v1`. Canonical JSON fingerprints freeze
disjoint repair splits in `data/manifests/repair_freeze.json`; evaluator hashes
live separately in `data/benchmark/evaluation_freeze.json`. Repair verification
never opens evaluator assets. These public final tasks were inspected to build
the adapter; they are not a blind benchmark and may appear in model pretraining.

Mock repair emits unchanged source for final tasks. It never reads references or
pretends to be a trained repair model. C's bounded oracles use math.gcd, linear
first-match enumeration, and the prefix-balance property, not imported source or
evaluation files. The same oracle rules validate generated expectations.

## Reproduce the adapter and audit

Fetch an upstream checkout, check out the pinned revision, then run from VeriCode:

```powershell
.\.venv\Scripts\python.exe scripts/import_quixbugs.py --source path/to/pinned/QuixBugs
.\.venv\Scripts\python.exe scripts/audit_quixbugs.py --output artifacts/new-audit.json
```

The importer checks all reviewed upstream hashes before writing dataset outputs.
It reproduces the declared adaptation and freeze files; review changes before
committing. The audit invokes Docker for both buggy and reference code, never host
imports. It must find three passing references, confirmed cleanup, and the recorded
buggy failures/timeouts. A compact audit summary is versioned beside provenance;
full local audit logs are ignored artifacts. Rebuilding an image can change its ID.
