# Local repair interface

From the checkout root:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ui]"
.\.venv\Scripts\python.exe -m vericode.ui_launcher
```

Open http://127.0.0.1:8501. The launcher binds only to loopback, disables usage
telemetry and automatic browser launch, and accepts `--port` and `--data-root`.
Stop with Ctrl+C. Never expose this code-execution controller publicly.

Select a development task, strategy and execution backend. Mock execution does
not execute candidate code or tests; test outcomes remain unknown. Docker uses
the same executor, image verification and limits as the CLI. Start Docker's Linux
engine and build `docker build --tag vericode-runner:day2 sandbox` first.

Run repair to inspect source, replacement, diff, visible outcomes, attempt history,
generated-case decisions, usage and resource limits. Download the repair JSON
before changing inputs; changing configuration clears the old result. Records
remain in session memory unless downloaded.

Independent evaluation is a second action on a completed repair. It loads the
separate suite only then, links to the exact repair record and never supplies
its observations to a provider. Its JSON is separately downloadable. Null counts,
tokens or outcomes mean unknown. API cost excludes local compute.

Unconfirmed cleanup blocks further jobs in the session. Inspect Docker and remove
only the identified VeriCode job before starting a new session; restarting the
interface alone does not repair a failed cleanup.

The default scripted fixtures demonstrate the controller and finite-test failure
modes, not language-model repair ability. The UI shares `direct_run`,
`feedback_run`, `augmented` and `scoring` with the CLI.

Headless interaction tests use
[Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
