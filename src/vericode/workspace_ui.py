"""Local repair workspace. Presentation shares the existing CLI controllers."""

import argparse
from dataclasses import asdict
import csv
from html import escape
import io
import json
from pathlib import Path

import streamlit as st

from vericode import ui_service
from vericode.checkpoints import fingerprint
from vericode.feedback import FeedbackLimits
from vericode.local_provider import require_local_model
from vericode.model_calls import TransportError
from vericode.model_io import GenerationLimits
from vericode.run_config import AugmentedConfiguration, FeedbackConfiguration, RunConfiguration
from vericode.sandbox_policy import ExecutionLimits
from vericode.schemas import RepairTask, ValidationError
from vericode.ui_theme import THEME

ROOT = Path(__file__).resolve().parents[2]
COLAB = "https://colab.research.google.com/github/Hassaan-Ahmad906/VeriCode-AI-debugging-and-repair-agent/blob/master/notebooks/train_free_colab.ipynb"
PAGES = {"Repair workbench": ":material/code:", "Run history": ":material/history:",
         "Model settings": ":material/tune:", "Training studio": ":material/model_training:",
         "Research & reports": ":material/analytics:"}


def html(value):
    st.markdown(value, unsafe_allow_html=True)


def heading(title, subtitle):
    html(f'<div class="crumb">Workspace <span>/</span> <b>{escape(title)}</b></div>'
         f'<div class="page-title">{escape(title)}</div><div class="page-subtitle">{escape(subtitle)}</div>')


def card(label, value, note):
    html(f'<div class="stat"><div class="stat-label">{escape(label)}</div><div class="stat-value">{escape(str(value))}</div><div class="stat-note">{escape(note)}</div></div>')


def sidebar():
    page = st.session_state.setdefault("page", "Repair workbench")
    with st.sidebar:
        html('<div class="brand"><div class="brand-mark">V</div>vericode<span>LAB</span></div>'
             '<div class="workspace-switch"><div class="avatar">VC</div><div><div class="workspace-name">Personal workspace</div><div class="workspace-detail">Local environment · Free</div></div></div>'
             '<div class="workspace-label">WORKSPACE</div>')
        for name, icon in PAGES.items():
            if st.button(name, key=f"nav_{name}", icon=icon, type="primary" if page == name else "secondary", width="stretch"):
                st.session_state["page"] = name
                st.rerun()
        html('<div class="workspace-label">PROJECT</div>')
        st.link_button("Documentation", "https://github.com/Hassaan-Ahmad906/VeriCode-AI-debugging-and-repair-agent#readme", icon=":material/menu_book:", width="stretch")
        html('<div class="sidebar-foot"><span class="live-dot"></span>Local workspace<br>API spending disabled<br><span style="color:#5f6f8b">VeriCode · Python repair lab</span></div>')
    return page


def execution_view(title, observation):
    if observation is None:
        st.caption(f"{title}: no execution recorded")
        return
    html(f'<div class="status-line"><span class="section-title">{escape(title)}</span><span class="pill">{escape(observation["status"])}</span></div>')
    cols = st.columns(4)
    for col, label, field in zip(cols, ("Passed", "Failed", "Errors", "Skipped"), ("tests_passed", "tests_failed", "tests_errors", "tests_skipped")):
        value = observation.get(field)
        col.metric(label, "—" if value is None else value)
    if observation.get("output"):
        with st.expander("Test output"):
            st.code(observation["output"], language="text")
    duration = observation.get("duration_seconds")
    st.caption(f"{'Unmeasured' if duration is None else f'{duration:.2f} s'} · Cleanup: {observation.get('cleanup_confirmed')} · {observation.get('detail', '')}")


def remember(repair, task):
    history = st.session_state.setdefault("run_history", [])
    history.insert(0, {"repair": repair, "score": None, "task": asdict(task)})
    del history[20:]


def results_view(repair):
    if repair is None:
        html('<div class="filebar"><strong>Repair output</strong><span>Awaiting a run</span></div>'
             '<div class="empty-result"><div class="empty-symbol">&lt;/&gt;</div><div class="empty-title">A clearer path to correct code</div>'
             '<div class="empty-copy">Run a repair to review the proposed change, test outcomes and reasoning history in one place.</div>'
             '<div class="flow"><b>Inspect</b>→<b>Repair</b>→<b>Verify</b></div></div>')
        return
    status = escape(repair["status"].replace("_", " "))
    tone = "pill-green" if repair["status"] == "visible_passed" else "pill-blue"
    html(f'<div class="status-line"><span class="section-title">Repair output</span><span class="pill {tone}">{status}</span></div>')
    patch_tab, code_tab, tests_tab, history_tab = st.tabs(["Patch diff", "Updated source", "Test results", "Attempts"])
    with patch_tab:
        st.code(repair.get("patch") or "No source change submitted.", language="diff")
        st.caption(repair["detail"])
    with code_tab:
        candidate = repair.get("candidate")
        st.code(candidate["replacement_source"] if candidate else "# No candidate submitted", language="python", line_numbers=True)
    with tests_tab:
        if "initial_execution" in repair:
            execution_view("Original source", repair["initial_execution"])
        execution_view("Final candidate", repair.get("repair_execution"))
    with history_tab:
        for attempt in repair["attempt_history"]:
            with st.expander(f"Attempt {attempt['attempt']} · {attempt['status']}"):
                st.json(attempt)
        if "test_generation" in repair:
            with st.expander("Generated-case decisions"):
                st.json(repair["test_generation"])
    st.download_button("Export repair record", json.dumps(repair, indent=2, allow_nan=False),
                       file_name=f"{repair['run_id']}-repair.json", mime="application/json", icon=":material/download:")


def evaluate_view(data_root, repair):
    with st.container(border=True):
        left, right = st.columns([4, 1.4], vertical_alignment="center")
        with left:
            html('<div class="section-title">Independent verification</div><div class="verification">Score the final patch against a separate suite. Results never return to the repair model.</div>')
        custom = repair is not None and repair["dataset_version"] == "custom-v1"
        disabled = repair is None or custom or st.session_state.get("cleanup_blocked", False)
        if right.button("Evaluate candidate", key="evaluate", disabled=disabled, icon=":material/verified_user:", width="stretch"):
            with st.spinner("Evaluating original and candidate independently…"):
                score = ui_service.evaluate_repair(data_root, repair)
            st.session_state["score"] = score
            for bundle in st.session_state.get("run_history", []):
                if bundle["repair"]["run_id"] == repair["run_id"]:
                    bundle["score"] = score
            if ui_service.cleanup_unconfirmed(score):
                st.session_state["cleanup_blocked"] = True
                st.rerun()
        if custom:
            st.caption("Custom input has no frozen independent suite. Visible-test success leaves independent correctness unknown.")
        score = st.session_state.get("score") if repair else None
        if score:
            html(f'<div class="notice"><strong>Independent suite: {escape(str(score["suite_passed"]))}</strong> · Agent accepted but failed: {escape(str(score["accepted_but_failed"]))}. Unknown outcomes remain unknown.</div>')
            original, candidate = st.columns(2)
            with original:
                execution_view("Original / independent suite", score["baseline_execution"])
            with candidate:
                execution_view("Candidate / independent suite", score["candidate_execution"])
            st.download_button("Export evaluation record", json.dumps(score, indent=2, allow_nan=False),
                               file_name=f"{score['evaluation_id']}-evaluation.json", mime="application/json")


def workbench(data_root):
    tasks = {task.task_id: task for task in ui_service.development_tasks(data_root)}
    top, action = st.columns([5, 1.15], vertical_alignment="bottom")
    with top:
        heading("Repair workbench", "Inspect a function. Review a patch. Verify the result.")
    with action:
        run = st.button("Run repair", key="run_repair", type="primary", icon=":material/play_arrow:",
                        disabled=st.session_state.get("cleanup_blocked", False), width="stretch")
        st.caption("Bounded execution")
    history = st.session_state.get("run_history", [])
    values = [("Repair runs", len(history), "Retained in this session"),
              ("Accepted patches", sum(row["repair"]["agent_accepted"] is True for row in history), "Visible checks only"),
              ("Model calls", sum(row["repair"]["usage"]["model_calls"] for row in history), "Actual transport invocations"),
              ("API spend", "$0.00", "Free local & scripted providers")]
    with st.container(key="run_metrics"):
        for column, value in zip(st.columns(4), values):
            with column:
                card(*value)
    with st.container(border=True):
        html('<div class="section-title">Run configuration</div>')
        c1, c2, c3, c4 = st.columns([1.5, 1.4, 1.2, 1.2])
        task_id = c1.selectbox("Development task", list(tasks), key="task_id")
        strategy = c2.selectbox("Strategy", ["direct", "feedback", "augmented"], key="strategy",
            format_func=lambda value: {"direct": "A · Direct repair", "feedback": "B · Feedback guided", "augmented": "C · Test augmented"}[value])
        backend = c3.selectbox("Execution", ["mock", "docker"], key="backend", format_func=lambda value: "Simulation" if value == "mock" else "Docker sandbox")
        provider = c4.selectbox("Model provider", ["mock", "ollama"], key="provider", format_func=lambda value: "Scripted demo" if value == "mock" else "Local Ollama")
        c1, c2 = st.columns([1.2, 2])
        input_mode = c1.selectbox("Input", ["development fixture", "custom function"], key="input_mode")
        model = c2.text_input("Local model tag", key="local_model_tag", disabled=provider == "mock")
        with st.expander("Advanced limits & resources"):
            a, b, c, d = st.columns(4)
            wall = a.number_input("Seconds per sandbox job", 0.5, 60.0, None if "limit_wall" in st.session_state else 10.0, step=0.5, key="limit_wall")
            attempts = b.number_input("Repair attempts (B/C)", 1, 10, None if "limit_attempts" in st.session_state else 3, key="limit_attempts")
            calls = c.number_input("Total model calls (B/C)", 1, 30, None if "limit_calls" in st.session_state else 6, key="limit_calls")
            tokens = d.number_input("Output token ceiling", 128, 8192, None if "limit_tokens" in st.session_state else 512, step=128, key="limit_tokens")
            st.caption("Docker: network disabled · 256 MiB memory · 0.5 CPU · 32 PIDs · bounded output and temporary space.")
    task = tasks[task_id]
    custom_ready = True
    left, right = st.columns([1, 1], gap="large")
    with left:
        with st.container(border=True):
            html('<div class="filebar"><strong>solution.py</strong><span>PYTHON 3 · SINGLE FILE</span></div>')
            source_tab, spec_tab, visible_tab = st.tabs(["Source code", "Specification", "Visible tests"])
            if input_mode == "custom function":
                with source_tab:
                    entry_point = st.text_input("Function name", "add", key="custom_entry_point")
                    source = st.text_area("Buggy Python source", "def add(a, b):\n    return a - b\n", height=260, max_chars=32768, key="custom_source")
                with spec_tab:
                    specification = st.text_area("Specification", "Return the sum of two integers.", height=200, max_chars=32768, key="custom_specification")
                with visible_tab:
                    tests = st.text_area("Visible pytest tests", "from solution import add\n\ndef test_add():\n    assert add(2, 3) == 5\n", height=240, max_chars=32768, key="custom_tests")
                task = RepairTask(1, "custom-v1", "custom_function", "development", specification, entry_point, "solution.py", source, tests)
                if provider != "ollama":
                    st.warning("Choose Local Ollama for custom code. The scripted provider only repairs known fixtures.")
                    custom_ready = False
                if strategy == "augmented":
                    st.warning("Custom code supports A/B. C requires a reviewed oracle for generated expected values.")
                    custom_ready = False
            else:
                with source_tab:
                    st.code(task.source, language="python", line_numbers=True)
                    st.caption("Original fixture · choose Custom function to paste your own code")
                with spec_tab:
                    st.write(task.specification)
                with visible_tab:
                    st.code(task.repair_tests, language="python", line_numbers=True)
    cls = {"direct": RunConfiguration, "feedback": FeedbackConfiguration, "augmented": AugmentedConfiguration}[strategy]
    options = dict(provider=provider, model=model if provider == "ollama" else "scripted-v1", backend=backend,
                   generation=GenerationLimits(output_tokens=tokens, max_transport_calls=1 if provider == "ollama" else 3,
                   request_timeout_seconds=30 if provider == "ollama" else 15), execution=ExecutionLimits(wall_seconds=wall))
    if strategy != "direct":
        options["feedback"] = FeedbackLimits(attempts, calls)
    config = cls(**options)
    selection = fingerprint({"task": asdict(task), "configuration": config.to_dict()})
    if st.session_state.get("selection") != selection:
        st.session_state["selection"] = selection
        st.session_state.pop("repair", None)
        st.session_state.pop("score", None)
    if run and custom_ready:
        st.session_state.pop("repair", None)
        st.session_state.pop("score", None)
        with st.spinner("Running repair within the configured limits…"):
            repair = ui_service.repair_task(task, config)
        st.session_state["repair"] = repair
        remember(repair, task)
        if ui_service.cleanup_unconfirmed(repair):
            st.session_state["cleanup_blocked"] = True
            st.rerun()
    repair = st.session_state.get("repair")
    with right:
        with st.container(border=True):
            results_view(repair)
    if backend == "mock":
        html('<div class="notice"><strong>Simulation mode</strong> · Candidate code and tests are not executed. Choose Docker sandbox for observed test outcomes. Scripted responses do not measure AI capability.</div>')
    elif provider == "mock":
        html('<div class="notice"><strong>Scripted provider + real sandbox</strong> · Docker observes the tests; the proposed repair is a predefined demonstration.</div>')
    evaluate_view(data_root, repair)
    if repair:
        with st.expander("Usage ledger & run configuration"):
            st.json(repair["usage"])
            st.json(repair["configuration"])
            st.caption("Null means unknown. Token ceilings are not measured usage. API cost excludes local compute.")
    html('<div class="guard"><span class="guard-icon">◇</span>Isolated execution. Separate evaluation. Traceable records.<br>Visible-test success is evidence about those tests, not proof of correctness.</div>')


def history_page():
    heading("Run history", "Inspect the repairs and evaluation records from this workspace session.")
    history = st.session_state.get("run_history", [])
    if not history:
        with st.container(border=True):
            html('<div class="empty-result"><div class="empty-symbol">↺</div><div class="empty-title">Your first run starts in the workbench</div><div class="empty-copy">Completed repairs will appear here with their configuration, usage and independent outcome. No sample results are presented as your own.</div></div>')
        return
    st.caption("Up to 20 recent runs in memory. Export records before ending this browser session.")
    for bundle in history:
        repair, score = bundle["repair"], bundle["score"]
        with st.expander(f"{repair['task_id']} · {repair['strategy'].upper()} · {repair['status']} · {repair['created_at_utc'][:19]}"):
            results_view(repair)
            st.json(repair["usage"])
            if score:
                st.caption(f"Independent suite passed: {score['suite_passed']}")
                st.json(score, expanded=False)


def models_page():
    heading("Model settings", "Connect an installed local model. Keep inference and credentials under your control.")
    left, right = st.columns([1.4, 1])
    with left:
        with st.container(border=True):
            html('<span class="pill pill-blue">LOCAL INFERENCE</span><div class="model-name">Ollama runtime</div><div class="model-copy">A small quantized coding model runs on your CPU. No API key or paid subscription is needed.</div>')
            st.text_input("Installed model tag", key="local_model_tag")
            st.code("127.0.0.1:11434", language="text")
            if st.button("Check local model", icon=":material/cable:"):
                try:
                    require_local_model(st.session_state["local_model_tag"], 5)
                    st.success("Local model is installed and available.")
                except (TransportError, ValidationError):
                    st.error("Model unavailable. Start the local runtime and install the configured tag. Cloud aliases are disabled.")
            st.caption("4 CPU threads · 4096 context · Cloud disabled · No redirects or proxy routing")
    with right:
        with st.container(border=True):
            html('<span class="pill">DEVELOPMENT</span><div class="model-name">Scripted demo</div><div class="model-copy">Reproducible fixture repairs for tests and demonstrations. It makes no language-model inference and needs no model download.</div>')
            st.caption("Available offline · Unknown token counts · $0 API cost")
    with st.container(border=True):
        html('<div class="section-title">Bring your own API</div><div class="section-note">Hosted adapters are disabled under the selected free-only policy. No key is saved or transmitted.</div>')
        first, second = st.columns(2)
        first.text_input("Hosted API model", disabled=True, placeholder="Requires an enabled, budgeted hosted adapter")
        second.text_input("API key", type="password", disabled=True, placeholder="Not required for local models")
        st.caption("A future hosted connection needs a provider, pricing and an explicit spending policy. Keys never belong in chat, run records or Git.")


def training_page():
    heading("Training studio", "Customize a small coding model using an available free cloud GPU.")
    html('<div class="notice"><strong>Ready to configure · not trained yet</strong> · Sign in to your Google account and start a free GPU session in Colab. GPU availability is not guaranteed; no paid compute is enabled.</div>')
    steps = [("01", "Prepare", "120 self-authored training examples. 24 validation examples. Operation families stay in separate splits."),
             ("02", "Fine-tune", "4-bit LoRA, rank 8. A two-step smoke check, then up to 3 epochs with early stopping."),
             ("03", "Export & verify", "Save the adapter, merge with its exact base, export a quantized GGUF and verify repairs in Docker.")]
    for column, (number, title, copy) in zip(st.columns(3), steps):
        with column:
            html(f'<div class="model-card"><span class="step-number">{number}</span><div class="model-name">{title}</div><div class="model-copy">{copy}</div></div>')
    with st.container(border=True):
        left, right = st.columns([3, 1.5], vertical_alignment="center")
        with left:
            html('<div class="section-title">VeriCode adapter · free GPU notebook</div><div class="section-note">Qwen2.5-Coder 1.5B Instruct · NF4 · q/v adapters · Saved model/data provenance</div>')
        right.link_button("Open Colab notebook", COLAB, type="primary", icon=":material/open_in_new:", width="stretch")
        st.caption("This customizes an existing pretrained model. It does not train a foundation model from scratch, and reduced loss does not establish better repairs.")
    st.link_button("Read training and export instructions", "https://github.com/Hassaan-Ahmad906/VeriCode-AI-debugging-and-repair-agent/blob/master/docs/training.md")


def research_page():
    heading("Research & reports", "Traceable engineering evidence, with measurement claims kept explicit.")
    html('<div class="notice"><strong>Scripted study evidence</strong> · The archived A/B/C comparison contains 19 mock calls and zero paid calls. It does not measure language-model repair performance.</div>')
    path = ROOT / "reports/day6/analysis/summary.csv"
    if path.exists():
        rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
        table = [{key: row[key] for key in ("split", "strategy", "tasks", "evaluation_passed", "evaluation_failed", "evaluation_unknown", "mock_calls")} for row in rows]
        st.dataframe(table, hide_index=True, width="stretch")
        st.download_button("Download complete summary CSV", path.read_bytes(), file_name="vericode-summary.csv", mime="text/csv")
    st.link_button("Read the research report", "https://github.com/Hassaan-Ahmad906/VeriCode-AI-debugging-and-repair-agent/blob/master/reports/research_report.md")
    st.link_button("Inspect evidence and failure analysis", "https://github.com/Hassaan-Ahmad906/VeriCode-AI-debugging-and-repair-agent/tree/master/reports/day6")
    st.caption("Three tasks per split · Inspected public benchmark subset · Unknown outcomes retained · Finite tests · Local-only container execution")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args, _ = parser.parse_known_args()
    st.set_page_config(page_title="VeriCode · Repair workspace", page_icon="V", layout="wide")
    html(THEME)
    # Preserve settings/custom input when their widgets are absent on another
    # page. Streamlit otherwise deletes widget-owned state after navigation.
    for key in ("task_id", "strategy", "backend", "provider", "input_mode", "local_model_tag",
                "custom_entry_point", "custom_source", "custom_specification", "custom_tests",
                "limit_wall", "limit_attempts", "limit_calls", "limit_tokens"):
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    st.session_state.setdefault("local_model_tag", "qwen2.5-coder:1.5b")
    page = sidebar()
    if st.session_state.get("cleanup_blocked", False):
        st.error("Container cleanup is unconfirmed. Jobs are blocked. Verify cleanup before restarting this local session.")
    try:
        if page == "Repair workbench":
            workbench(args.data_root)
        elif page == "Run history":
            history_page()
        elif page == "Model settings":
            models_page()
        elif page == "Training studio":
            training_page()
        else:
            research_page()
    except (ValidationError, OSError) as exc:
        st.error(str(exc))
