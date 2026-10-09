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
