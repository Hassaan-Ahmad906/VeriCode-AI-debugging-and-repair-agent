# Test-augmented repair C

`vericode augment --task sum_positive` runs offline. Add `--backend docker` to
execute visible and accepted generated tests in the existing constrained runner.
Test generation uses one structured response with bounded transport retries. Its
calls count against C's shared call ceiling before B's bounded repair loop starts.
The default ceiling is six total calls; it does not compute-match A or B.

The model proposes at most eight JSON `{args, expected}` cases, never executable
test source. A trusted controller checks argument shape/size and expected values
against versioned rules derived from reviewed specifications. For development
fixtures these are positive-element arithmetic, explicit ASCII vowel enumeration,
and piecewise clamping. No buggy/reference implementation or evaluator file is
executed to determine an expectation. Unsupported domains fail closed.

Only accepted cases become literal assertions. Original visible tests are retained;
test-name collisions, duplicate arguments, wrong expectations, extra fields, and
oversized augmented suites are discarded with a reason. Model-generated strings
become quoted data, not Python expressions. Rendered tests and candidates execute
only in Docker, never on the host. AST parsing on the host is validation only.

Each C record includes the generation prompt/version, oracle version, every case
decision, generated-test hash, generation usage, repair history, and globally
numbered calls with a purpose. Malformed generation envelopes stop and retain
usage. If no case is accepted, B continues with the original visible tests and the
remaining budget. Mock execution records unknown outcomes; it never pretends the
augmented suite passed. Independent scoring remains outside the repair loop.
