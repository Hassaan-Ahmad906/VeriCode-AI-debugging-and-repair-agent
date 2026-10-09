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

Planned flow: repair input → provider → candidate validation → isolated working
copy → visible execution feedback → bounded revisions → final candidate.
Independent evaluation receives that final candidate and its own test suite.
Evaluation feedback never returns to the repair provider.

Day 1 separates data by API and object shape, not operating-system permissions.
The trusted controller can read both fixture trees. The model will have no shell
or filesystem tools. Day 2 must mount/copy only the approved inputs into each job,
never the repository root, evaluation directory during repair, or credentials.
