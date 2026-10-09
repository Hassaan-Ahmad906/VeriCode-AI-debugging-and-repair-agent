# Current limitations

- Day 1 has no sandbox runner, live model adapter, repair strategies, independent
  scoring, or measured repair results. Mock execution must never report test passes.
- Three hand-authored development fixtures are a small, nonrepresentative sample.
  Their expected values were reviewed from specifications, but candidate/test
  behaviour has not yet been run in isolation. No final benchmark is selected.
- File separation and typed interfaces protect the intended context flow, but are
  not a security boundary against a compromised host controller. Container
  restrictions are Day 2 work; containers reduce risk without guaranteeing safety.
- Public evaluation-only tests are unavailable during repair by design, not secret
  from people or model pretraining. Future public benchmarks may be contaminated.
- Passing any finite test suite is not proof of correctness. Small samples, test
  coverage, model nondeterminism, and single-file scope limit generalisation.
- Direct dependencies are pinned; transitive dependencies are not locked across
  platforms. Setup currently needs package-index access. This is a local-only
  project and is not ready for a public execution service or a release tag.
