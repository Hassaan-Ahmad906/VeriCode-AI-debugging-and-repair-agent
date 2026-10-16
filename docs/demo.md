# Two-minute local demonstration

Before presenting: install `.[dev,ui]`, start the Docker Linux engine, build the
runner image, and launch `python -m vericode.ui_launcher`. Use a localhost browser.
The scripted demonstration needs no model download, API key or paid service.

- **0:00–0:25:** Explain the question: do feedback/additional tests help relative
  to actual cost? Show `sum_positive`, its specification and narrow visible tests.
  Select provider mock, Docker execution and strategy feedback (B).
- **0:25–0:50:** Run repair. B accepts the original source because the visible
  tests pass. Show zero repair calls and unchanged source. Explain that no live
  language model was called and visible success is not correctness.
- **0:50–1:10:** Evaluate the final candidate separately. Show the independent
  failure. Explain that these observations cannot reach the repair controller.
- **1:10–1:40:** Select augmented (C), run repair and then evaluate. Show the
  independently checked negative-input case, scripted patch, observed Docker
  outcomes, call ledger and extra generation cost. Do not claim measured LLM gains.
- **1:40–2:00:** Show JSON downloads and the traceable report. Mention three tasks
  per split, unknown timeouts, public benchmark contamination, finite-test limits
  and container limits. The free local model and optional Colab adapter training
  are extensions, with results labeled separately from this scripted evidence.

Optional local-model demonstration: start Ollama with cloud disabled, choose an
installed model tag, provider ollama and Docker, then paste a simple custom buggy
function in custom-input mode. CPU latency and model success are not guaranteed;
retain errors and failed outcomes. No independent suite exists for arbitrary
custom input. A/B work there; C requires a reviewed independent expected-value
oracle.
