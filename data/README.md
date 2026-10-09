# Self-authored development fixtures, v1

These three synthetic tasks were authored for VeriCode, not copied from a
benchmark. Tests are stored as text and must only run inside an approved sandbox.
They cover positive sums, ASCII vowel counting, and integer clamping. Expected
values were determined directly from the specifications by arithmetic and
enumeration; they are not observations from the buggy functions.

`repair/<id>/task.json` is the complete repair-visible input. The evaluator alone
loads `evaluation/<id>/suite.json`. Manifests specify fixed task IDs and versions.
The final manifest is intentionally empty: these tasks are for implementation and
prompt development, never final performance reporting. Do not silently reuse them
as an evaluation task split. Evaluation-only **tests** and final-evaluation
**tasks** are separate concepts.

The visible tests deliberately miss some faults. In particular, `sum_positive`
and `count_vowels` already satisfy their visible examples; this supports later
overfitting checks. Nothing has been executed or empirically validated on Day 1.
The evaluator fixtures are in the public repository, so they are not secret;
the boundary is their absence from agent context and candidate workspaces.

QuixBugs is deferred to Day 5. No external benchmark content has been imported.
