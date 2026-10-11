# Current limitations

- The local Docker runner and visible-test smoke checks work. There is still no
  live model adapter, repair strategy A/B/C, independent scoring, or measured
  live-model repair result. Mock execution must never report test passes.
- Three hand-authored development fixtures are a small, nonrepresentative sample.
  Expected values were reviewed from specifications. Original/mock-patched clamp
  visible tests have now run in isolation. Evaluation fixtures have not run, and
  no final benchmark is selected.
- File separation and typed interfaces protect the intended context flow, but are
  not a security boundary against a compromised host controller. Container
  restrictions and their verification are documented in `sandbox.md`; containers
  reduce risk without guaranteeing safety. Pytest and candidate share an interpreter,
  so malicious code may falsify test reports even while contained.
- Public evaluation-only tests are unavailable during repair by design, not secret
  from people or model pretraining. Future public benchmarks may be contaminated.
- Passing any finite test suite is not proof of correctness. Small samples, test
  coverage, model nondeterminism, and single-file scope limit generalisation.
- Direct dependencies are pinned; transitive dependencies are not locked across
  platforms. Setup currently needs package-index access. This is a local-only
  project and is not ready for a public execution service or a release tag.
