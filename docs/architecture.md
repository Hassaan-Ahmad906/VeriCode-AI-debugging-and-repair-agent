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
in the Day 1 application is a fixed `git rev-parse HEAD` metadata query, with a
two-second timeout and no candidate-controlled arguments.

Future flow adds sandbox execution, visible feedback, and bounded revisions before
final independent evaluation. Evaluation feedback never returns to the provider.

Day 1 separates data by API and object shape, not operating-system permissions.
The trusted controller can read both fixture trees. The model will have no shell
or filesystem tools. Day 2 must mount/copy only the approved inputs into each job,
never the repository root, evaluation directory during repair, or credentials.
