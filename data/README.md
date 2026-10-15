# Self-authored development fixtures, v1

These three synthetic tasks were authored for VeriCode, not copied from a
benchmark. Tests are stored as text and must only run inside an approved sandbox.
They cover positive sums, ASCII vowel counting, and integer clamping. Expected
values were determined directly from the specifications by arithmetic and
enumeration; they are not observations from the buggy functions.

`repair/<id>/task.json` is the complete repair-visible input. The evaluator alone
loads `evaluation/<id>/suite.json`. Manifests specify fixed task IDs and versions.
These tasks are for implementation and prompt development, never final performance
reporting. The final manifest now selects a disjoint pinned QuixBugs subset.
Evaluation-only **tests** and final-evaluation
**tasks** are separate concepts.

The visible tests deliberately miss some faults. In particular, `sum_positive`
and `count_vowels` already satisfy their visible examples; this supports later
overfitting checks. On Day 2, original/scripted-patched clamp visible tests ran
inside Docker. Day 5 adds independent-suite smoke checks; these engineering
observations are separate from final LLM benchmark measurement.
The evaluator fixtures are in the public repository, so they are not secret;
the boundary is their absence from agent context and candidate workspaces.

Day 5 adds three final `quix_*` tasks with unchanged upstream buggy source,
attribution, source hashes, explicit adaptations, and reference audits. See
[benchmark review](../docs/benchmark.md). Frozen repair identities are separate
from evaluator-suite hashes; neither references nor evaluator data enter requests.
