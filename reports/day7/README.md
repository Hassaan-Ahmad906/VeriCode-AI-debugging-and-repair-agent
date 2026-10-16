# Local model integration checks

The laptop now runs the official Ollama 0.40.5 CPU runtime with cloud disabled and
the installed `qwen2.5-coder:1.5b` quantized pretrained model. The official runtime
asset SHA-256 was verified before extraction. Weights/binaries remain ignored.

All declared local attempts are preserved under `local-model`, with exact file
hashes and the installed model manifest. These are development checks with local
source edits and adapter changes, not a frozen or fair A/B experiment:

| Trial | Result | Model calls | Input/output tokens |
|---|---|---:|---:|
| Initial JSON-only A | Wrong fields rejected; no execution | 1 | 248 / 189 |
| Structured-schema A | Unchanged source; visible and independent suites fail | 1 | 248 / 48 |
| Structured-schema B | Changed patch; 2 visible and 3 independent tests pass | 1 | 487 / 65 |
| Redesigned UI B | Changed patch; 2 visible and 3 independent tests pass | 1 | 487 / 65 |

Total: four real local inference calls, 1,470 reported input tokens, 367 reported
output tokens, $0 API cost. Local electricity/compute are not priced. Two repair
trials succeeded on the same single development fixture; the second verifies UI
integration and is not an independent task. Failed trials are retained. No claim
of general repair ability, method superiority or fine-tuning improvement follows.

Evaluation records link to the exact saved repair hashes and make zero model
calls. All candidate execution occurred in constrained Docker containers with
confirmed cleanup. The raw evaluator configuration retains the CLI's default
mock provider metadata, but evaluation itself uses no provider; its backend is
Docker and its execution observations are real.

The first trial used JSON-only decoding. Later trials used a strict candidate
schema plus the same task/feedback prompt contracts. Source was locally edited
on recorded HEAD `546f540`; the records explicitly warn that HEAD alone does not
identify those edits. The current adapter hash is saved as supporting metadata,
not retroactively asserted to identify every trial's source. Model tags remain
mutable outside the archived manifest. Keep these records separate from Day 6's
frozen scripted studies.

Cloud LoRA training has **not run**. Its notebook requires the owner to sign in
to Colab and start an available free GPU runtime. The training/export scripts and
dataset checks are prepared; no adapter weights or training-loss measurements are
invented. See [training instructions](../../docs/training.md).
