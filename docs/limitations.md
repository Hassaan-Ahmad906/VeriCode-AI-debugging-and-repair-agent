# Current limitations

- The local Docker runner, A/B/C and independent scoring work with scripted mocks.
  There is no live model adapter or measured live-model repair result. Mock
  execution must never report test passes.
- Direct repair A now works with scripted mock proposals. It observes visible tests
  only after proposal and cannot measure model ability. Network adapters and
  enforceable spending caps are absent; the transport timeout is an adapter contract.
- Batch checkpoints provide conservative local resumption, not exactly-once remote
  calls or authenticated provenance. Interrupted starts and stale locks require
  inspection. Source-byte/runtime changes invalidate resume; immutable Docker images
  must remain locally available. Repair records keep evaluator results separate.
- Three hand-authored development fixtures are a small, nonrepresentative sample.
  Expected values were reviewed from specifications. Original/mock-patched clamp
  visible/evaluation suites have run in isolation. Three pinned QuixBugs final tasks
  form a deliberately small adapted subset, not the full or a blind benchmark.
- File separation and typed interfaces protect the intended context flow, but are
  not a security boundary against a compromised host controller. Container
  restrictions and their verification are documented in `sandbox.md`; containers
  reduce risk without guaranteeing safety. Pytest and candidate share an interpreter,
  so malicious code may falsify test reports even while contained.
- Verification covers Docker Desktop's WSL2/cgroup v2 engine. Preflight rejects
  cgroup v1 and missing controls. Host/controller suspension or failure may delay
  watchdogs/cleanup; CPU quota was inspected, not benchmarked across scheduler loads.
- Public evaluation-only tests are unavailable during repair by design, not secret
  from people or model pretraining. Future public benchmarks may be contaminated.
- Passing any finite test suite is not proof of correctness. Small samples, test
  coverage, model nondeterminism, and single-file scope limit generalisation.
- Direct dependencies are pinned; transitive dependencies are not locked across
  platforms. Setup currently needs package-index access. This is a local-only
  project and is not ready for a public execution service or a release tag.
- Feedback repair B works with scripted responses and real Docker observations.
  It may accept an unchanged buggy original whose visible tests pass. Deterministic
  response fixtures verify revision/control flow, not model reasoning or an A/B
  performance improvement. Exact-source repetition only detects textual cycles.
  Output clipping loses context; untrusted test output can still attempt prompt
  injection despite the restricted fields and instruction. No feedback prompt has
  been evaluated against a live model. Journal limits are finite; a full journal
  stops before another task rather than discarding history.
- C validates expectations against reviewed bounded rules, not model agreement.
  Coverage remains narrow and oracle mistakes remain possible. Reference audits
  are engineering checks; public data and inspected final-task adapters limit any
  future claim about unseen-task generalisation. No final LLM measurement exists.
- Day 6's development pilot and final-split demonstration use scripted/no-op mocks,
  with separate complete evidence and no paid calls. Unknown final outcomes remain
  unresolved. Tables/figures trace engineering observations; they cannot establish
  an A/B/C model effect, significance, novelty or compute matching. Local timing is
  machine dependent; API-zero cost excludes Docker compute. Optional plotting
  versions are snapshotted but transitive dependencies are not universally locked.
