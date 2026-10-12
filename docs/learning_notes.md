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
