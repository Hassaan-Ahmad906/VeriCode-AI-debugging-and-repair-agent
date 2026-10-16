# Local prototype release criteria

Version 0.1.0 is a local engineering prototype. It is not a trained foundation
model, a public execution service, or a measured repair-effectiveness result.
GPU training and export remain unexecuted recipes until a user starts Colab.
A repository-wide license for original code has not been selected; see NOTICE.

Tag only after these required local checks pass:

- Clean intended commit and verified matching GitHub branch; no credentials,
  model weights, runtime binaries or transient run artifacts committed.
- Editable installation from a fresh virtual environment with `.[dev,ui,analysis]`;
  dependency consistency, CLI help/demo and optional UI startup work.
- Full automated suite, including explicit Linux Docker integration, passes.
  Offline CI runs without model credentials, inference or GPU. Dependency
  installation and Docker image builds may need internet access.
- Streamlit interactions cover repair/evaluator separation, stale result removal
  and cleanup blocking; localhost HTTP health check passes. CLI mock remains the
  default; the UI starts on Overview and offers local model/Docker by default.
- Official runtime download checksum passes; a real free CPU model can return a
  bounded structured repair, and Docker observes its candidate tests. Preserve
  failures and actual usage; a model success is a smoke check, not a benchmark.
- Historical evidence remains byte-identical; report distinguishes scripted,
  local-model and missing cloud-training observations. QuixBugs attribution and
  base-model licensing are documented. Fresh setup and two-minute demo are written.
- Training data/split/masking/notebook structure checks pass. Self-authored target
  examples pass inside Docker. No GPU training quality is claimed without a run.

Fresh Windows PowerShell setup from this checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ui,analysis]"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m vericode demo --task clamp
.\.venv\Scripts\python.exe -m vericode.ui_launcher
```

For actual candidate execution, start Docker Desktop's Linux engine, then:

```powershell
docker build --tag vericode-runner:day2 sandbox
.\.venv\Scripts\python.exe -m vericode sandbox-info
.\.venv\Scripts\python.exe -m pytest --run-docker -q
```

On Linux/macOS use `.venv/bin/python` and quote extras as `'.[dev,ui,analysis]'`.
The CLI package does not bundle repository fixture data: run from the checkout
or supply `--data-root`. The UI launcher accepts that option too. The wheel
contains the Python application, not Docker/weights/data. Direct dependencies
are pinned; transitive resolution is not a complete environment lock.

See [local model setup](local-model.md), [UI guide](ui.md),
[two-minute demo](demo.md) and [free GPU training](training.md).
CI workflow runs are separately observable in GitHub Actions; locally passing
checks do not imply a remote CI run has passed.
