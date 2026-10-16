# VeriCode: a local program-repair experiment harness

## Question and current evidence

How do execution feedback and independently checked additional tests affect
Python repair outcomes relative to their actual model calls, tokens and cost?
VeriCode implements this comparison for small, single-file functions. The saved
Day 6 observations use scripted providers, not language models. They establish
that the controller, isolation, logging and independent evaluator work together;
they cannot establish LLM repair effectiveness, novelty or research readiness.

## Methods

A requests one replacement, then observes visible tests without revision. B first
runs visible tests and revises only when needed, within attempt/call ceilings.
C proposes extra data-only cases, checks expected values against reviewed bounded
specification rules, and runs B on the accepted tests. Invalid cases are retained
as discarded decisions. Generation and transport retries consume the shared call
ceiling. Different stopping conditions produce different actual compute use.

Candidate replacement targets only `solution.py`; AST validation rejects invalid
syntax and unsupported targets. Candidate functions and tests run only inside
Docker with no network, non-root identity, read-only root, dropped capabilities,
CPU/memory/PID/time/output limits and bounded temporary filesystems. The sandbox
receives source/test contents, no evaluator assets, credentials or host mounts.
Unconfirmed cleanup halts dependent jobs. Docker reduces risk, but is not a
complete security boundary; the application is a local research tool.

Repair-visible and independent test suites are separate. A post-repair evaluator
tests both original and submitted sources without making provider calls. It
retains failed assertions, timeouts, test errors, infrastructure failures and
unsubmitted candidates as distinct observations. A missing candidate is not
silently replaced by the original source. Agent acceptance is separate from
independent suite success. Finite-test success is not proof of correctness.

Three self-authored development tasks and three reviewed QuixBugs tasks form
disjoint task manifests. QuixBugs is pinned to
`4257f44b0ff1181dedaedee6a447e133219fcebf`. Visible/evaluator adaptations,
reference audit, license and excluded files are documented in
[benchmark notes](../docs/benchmark.md). This is an inspected, selected subset;
its public content may already be present in pretrained models' training data.

Frozen protocols record source/runtime/configuration/data identities before
collection. Every repair completes before scoring starts. Append-only journals
record starts and outcomes with hashes; incomplete or ambiguous starts cannot be
silently replayed. Archived journals and analysis contain exact row-to-event and
repair-to-score links. Historical evidence is not rewritten when code changes.

## Saved scripted observations

Each method/split has three tasks. Calls below are **mock transport invocations**.
All test observations in this table came from Docker. Final-task mocks deliberately
return unchanged source; they are not attempts by a language model.

| Split | Method | Passed | Assertion failures | Unknown | Mock calls |
|---|---|---:|---:|---:|---:|
| Development | A | 3 | 0 | 0 | 3 |
| Development | B | 1 | 2 | 0 | 1 |
| Development | C | 3 | 0 | 0 | 6 |
| Final subset | A | 0 | 2 | 1 | 3 |
| Final subset | B | 0 | 2 | 1 | 0 |
| Final subset | C | 0 | 0 | 3 | 6 |

B accepts the original development sum/vowel functions because their narrow
visible suites pass; both then fail independently. C's independently justified
boundary cases expose those bugs in this scripted demonstration. This illustrates
test insufficiency and the need for an independent oracle. It is not evidence
that C generally outperforms B with real models.

Final A/B each retain one timeout as unknown, not an assertion failure or a pass.
Final C submits no candidates after repeated unchanged proposals, leaving all
three outcomes unknown. The denominator retains all tasks. There are no known
baseline-passing suites with a known candidate outcome, so the suite-level
regression rate is undefined. Zero observed regressions proves no absence of
per-test regressions.

Across these archived studies: 19 mock calls, zero paid calls, API cost $0.
Tokens are unknown except for zero-call runs, which consume none. Local compute
cost is not priced. Shared ceilings do not make the methods compute-matched.
Exact timing, failure cases, payload hashes, event lines, CSV and standalone
figures are in the [traceable analysis](day6/analysis/report.md).

## Local model and training extension

The free-only extension supports a local pretrained Ollama model with configurable
tag and custom function inputs; it remains separate from the frozen mock study.
The laptop has about 16 GB RAM and no NVIDIA GPU. A free Colab LoRA recipe prepares
small custom adapter training on self-authored expression repairs. No completed
cloud training, validated trained export or measured fine-tuning improvement is
claimed. See [training instructions](../docs/training.md). Training loss must not
be substituted for independent execution accuracy.

## Related work and limitations

[Self-Debugging](https://arxiv.org/abs/2304.05128) studies model revision using
feedback and explanations. It motivates evaluating execution-informed revision;
VeriCode does not reproduce its experimental setup or results.
[EvalPlus](https://arxiv.org/abs/2305.01210) studies stronger code-evaluation tests,
motivating scrutiny of narrow-suite success. Its benchmark and test generator are
not imported here. [QuixBugs](https://jkoppel.github.io/QuixBugs/quixbugs.pdf)
provides the external program-repair benchmark; VeriCode uses only the explicitly
reviewed Python subset, not the full benchmark.

The current evidence is limited by scripted responses, three tasks per split,
manual subset inspection, finite expected-value rules, shared public data,
unknown tokens, hardware-specific timings and suite-level metrics. Test output
is untrusted; prompting alone does not prevent injection. Pytest shares a Python
interpreter with candidate code, so hostile code can interfere with reporting.
The Docker runner is unsuitable as a public arbitrary-code service.

A credible model comparison still needs an immutable model/adapter identity,
predeclared protocol, enough independent tasks, preserved failures and actual
usage, with paid work remaining disabled under the user's free-only policy.
The correct portfolio claim is a reproducible local engineering system with
explicit missing measurements, not a demonstrated improvement in LLM repair.
