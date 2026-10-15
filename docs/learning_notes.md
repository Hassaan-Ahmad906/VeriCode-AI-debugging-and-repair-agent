# Learning notes

## Packaging and repeatable development

An editable install connects the CLI to the source tree. A virtual environment
keeps project dependencies separate from system Python. Pinning direct dependency
versions makes setup more repeatable, but a full transitive lock is stronger.

## Data contracts and information boundaries

A frozen dataclass documents the fields a component receives and prevents normal
attribute mutation. Runtime validation rejects malformed external JSON; type hints
alone would not. Neither mechanism creates an operating-system security boundary.
The repair task intentionally cannot carry evaluator tests or paths.

## Tests versus evaluation

Visible tests guide repair; evaluation-only tests check whether the resulting
patch generalises beyond that feedback. Development/final task splits ask a
different question: did we tune the system on the tasks used to measure it?
Both separations matter. A mock result with `suite_passed: null` means no
measurement occurred, not failure and not success.

## Dependency inversion and honest mocks

The repair function depends on `ModelProvider.propose`, not a vendor SDK. A mock
implements that same contract with scripted responses, letting tests exercise
data flow and failure handling offline. These tests validate the controller, not
model ability or patch correctness. Tokens stay unknown; API spend is zero.

A temporary directory prevents ordinary patch application from changing source
fixtures, but cannot isolate executed Python from the host. Parsing an AST also
does not remove side effects. This is why the mock runner never executes code and
why an actual sandbox is the next session's prerequisite.

## Container lifecycle and outcomes

Docker's CPU quota and memory/PID limits apply to the container job. The watchdog
limits elapsed time; removing the whole container handles spawned descendants.
Stopping an attached Docker client alone merely disconnects the controller.
The trusted parent also has a Linux timer, independent of the host deadline.
Neither timer removes the need to verify cleanup or keep the controller/runtime
available. A local container is not a guarantee against every adversarial program.

Pass/fail counts are observations from pytest, not mathematical proofs. An empty
suite, skipped tests, collection errors, output overflow, and a broken runner must
not be folded into success. Cleanup failure is also an infrastructure failure:
the controller blocks further work and reports the exact job name for recovery.

The CLI smoke command demonstrates execution independently of model ability.
A scripted mock patch passing real visible tests is still a scripted demonstration.

## Direct repair and accounting

Strategy A produces one repair response without execution feedback. Running
visible tests afterward records an outcome; it does not revise the patch. A
transport failure can be retried with the identical request, but a malformed
answer is already a response and must not silently earn another try.

One usable response can therefore involve several actual model calls. Log all
calls and known charges, including failures. Unknown token or cost totals are
null; a known subtotal of zero does not establish a zero total. None of this
makes A/B/C compute-matched simply because they share an upper limit.

## Why checkpoint before a call?

A controller can crash after sending a request but before saving its response.
A durable start marks that uncertainty. Replaying it automatically could duplicate
work or hide unknown charges. A durable completed record lets resume skip the
task, including failures, while preserving the original experiment denominator.

A fingerprint freezes the inputs and code used by a batch. Checksums detect
accidental corruption but do not authenticate results. A directory lock prevents
cooperating controllers from overlapping; it is not a distributed transaction.
These are practical engineering controls for fair experiments, not perfect crash
or determinism guarantees.

## Feedback and stopping

B observes visible tests before its first repair and after each valid candidate.
A new repair prompt includes the latest source and bounded visible failure;
a transport retry sends the identical prompt. Both consume actual calls, but
only new repair requests consume repair attempts. A final-call transient error
is still a transport failure; a used-up budget never grants another call.

Stopping on an already-passing original can save every model call while leaving
a bug untouched. Weak visible tests explain this result. Repeating any previously
seen exact source cannot yield new deterministic test evidence, so stop before
running it again. Log that response's usage and preserve the last checked patch.
Stopping rules bound effort; only an independent evaluator can assess whether
visible acceptance overfits the available tests.

## Independent expectations and evaluation

A generated assertion is useful only if its expected value has support beyond the
same model or buggy program. VeriCode accepts bounded JSON inputs/expectations
against specification rules, then renders literal assertions. Agreement with the
buggy implementation is never the validator. Rejected cases remain in the log.

An independent evaluator runs after repair, on tests absent from its requests.
An accepted-but-failing patch exposes weak visible coverage. A regression requires
an observed original-suite pass followed by a candidate-suite failure. A timeout
has unknown suite outcome; retaining it in the denominator prevents silent
survivorship bias. Missing-outcome bounds are not statistical confidence intervals.
