# Architecture

The host controller loads repair-visible JSON into a frozen `RepairTask`.
It contains the specification, original source, visible tests, and one canonical
filename, `solution.py`. The loader reads bounded data; it never imports fixture
code. Unknown fields are rejected so evaluator fields cannot slip into the
repair-input contract.

`schemas.py` defines repair tasks and replacement candidates. `datasets.py` loads
repair inputs and fixed manifests. `results.py` distinguishes execution states
and nullable evaluation outcomes. `evaluation.py` separately loads evaluator
tests; future orchestration must call it only after repair is complete.

Day 1 flow: `cli.py` → `experiments.py` → `repair.py` → `ModelProvider.propose` →
`patches.py` → fresh staging directory → `MockExecutor` → chosen candidate.
Only then does the controller load the separate evaluation suite and record a
mock evaluation. `experiments.py` writes JSON with the prompt, patch, data version,
HEAD commit when available, usage, configuration, and explicit limitations.

`providers.py` defines the typed provider protocol and a deterministic mock.
The request contains only the allowlisted repair task. Canned mock responses are
demonstration configuration, not independently verified reference solutions.
`patches.py` checks task identity, the sole target, parseable Python, and the entry
function. Parsing does not prove code safe, executable, or semantically correct.
The provider is a trusted host-side adapter; the model itself has no file tools.

The staging directory is a host-side text workspace, **not an execution sandbox**.
It contains only `solution.py` and visible tests and is deleted on success or
exceptions. Mock execution does not import or run either file. The only subprocess
in the mock flow is a fixed Git HEAD metadata query, with a two-second timeout and
no candidate-controlled arguments. Its trust exception is limited to the editable
package's repository path.

Future flow adds sandbox execution, visible feedback, and bounded revisions before
final independent evaluation. Evaluation feedback never returns to the provider.

Day 1 separates data by API and object shape, not operating-system permissions.
The trusted controller can read both fixture trees. The model will have no shell
or filesystem tools. The Docker runner sends only approved source/visible-test
contents over stdin, never the repository root, evaluation directory during
repair, or credentials.

## Day 2 execution path

`jobs.py` creates an immutable `VisibleJob` from a task and optional validated
candidate. The executor receives two strings, not paths or evaluator objects.
`DockerExecutor` preflights daemon capabilities, resolves a local image ID,
creates and inspects a constrained job, and starts its trusted image harness.
The harness stages text on container tmpfs and runs pytest in a child with a fixed
environment. `processes.py` drains output with a hard retention limit and deadline.
Cleanup removes the whole container. An unconfirmed cleanup blocks that executor
from submitting more jobs.

`run-tests` serializes an engineering smoke-check record. `sandbox-info` verifies
prerequisites without executing candidate code. The older `demo` command remains
mock-only. Actual repair strategies and final evaluator orchestration come later.
