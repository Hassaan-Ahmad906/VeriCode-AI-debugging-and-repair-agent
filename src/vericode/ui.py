"""Optional local Streamlit interface. No submitted Python runs on the host."""

import argparse
import json
from pathlib import Path

import streamlit as st

from vericode import ui_service
from vericode.checkpoints import fingerprint
from vericode.feedback import FeedbackLimits
from vericode.model_io import GenerationLimits
from vericode.run_config import AugmentedConfiguration, FeedbackConfiguration, RunConfiguration
from vericode.sandbox_policy import ExecutionLimits
from vericode.schemas import ValidationError


def display_execution(label, execution):
    st.markdown(f"**{label}**")
    if execution is None:
        st.write("No execution recorded.")
        return
    st.write(f"Status: {execution['status']}")
    counts = {k: execution.get(k) for k in ("tests_passed", "tests_failed", "tests_errors", "tests_skipped")}
    st.json(counts, expanded=False)
    if execution.get("output"):
        st.code(execution["output"], language="text")
    st.caption(f"Duration: {execution.get('duration_seconds')} s · Cleanup confirmed: {execution.get('cleanup_confirmed')}")
    st.caption(execution.get("detail", ""))


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args, _ = parser.parse_known_args()
    st.set_page_config(page_title="VeriCode · Repair lab", page_icon="🔎", layout="wide")
    st.title("VeriCode")
    st.caption("A local lab for Python repair, execution feedback and independent evaluation")
    st.info("Scripted demo provider · $0 API cost · paid services disabled. Mock execution does not run tests.")
    try:
        tasks = {t.task_id: t for t in ui_service.development_tasks(args.data_root)}
        with st.sidebar:
            st.subheader("Repair configuration")
            task_id = st.selectbox("Development task", list(tasks), key="task_id")
            strategy = st.selectbox("Strategy", ["direct", "feedback", "augmented"], key="strategy")
            backend = st.selectbox("Execution", ["mock", "docker"], key="backend")
            st.caption("A: one response. B: visible feedback. C: independently checked extra cases + B.")
            wall = st.number_input("Seconds per sandbox job", 0.5, 60.0, 10.0, step=0.5)
            attempts = st.number_input("Repair attempts (B/C)", 1, 10, 3)
            calls = st.number_input("Total model calls (B/C)", 1, 30, 6)
            tokens = st.number_input("Output token ceiling", 128, 8192, 2048, step=128)
            st.caption("Docker: network off · 256 MiB · 0.5 CPU · 32 PIDs · bounded output and temporary space.")
        cls = {"direct": RunConfiguration, "feedback": FeedbackConfiguration, "augmented": AugmentedConfiguration}[strategy]
        options = dict(backend=backend, generation=GenerationLimits(output_tokens=tokens), execution=ExecutionLimits(wall_seconds=wall))
        if strategy != "direct":
            options["feedback"] = FeedbackLimits(attempts, calls)
        config = cls(**options)
        task = tasks[task_id]
        selection = fingerprint({"task": task.__dict__, "configuration": config.to_dict()})
        if st.session_state.get("selection") != selection:
            st.session_state["selection"] = selection
            st.session_state.pop("repair", None)
            st.session_state.pop("score", None)
        blocked = st.session_state.get("cleanup_blocked", False)
        if blocked:
            st.error("A job's cleanup could not be confirmed. Further execution is blocked. Verify Docker cleanup before restarting this local session.")
        st.subheader("Repair input")
        st.write(task.specification)
        left, right = st.columns(2)
        with left:
            st.caption("Original solution.py")
            st.code(task.source, language="python")
        with right:
            st.caption("Repair-visible tests")
            st.code(task.repair_tests, language="python")
        if st.button("Run repair", key="run_repair", type="primary", disabled=blocked):
            st.session_state.pop("repair", None)
            st.session_state.pop("score", None)
            with st.spinner("Running the bounded repair controller…"):
                repair = ui_service.repair_task(task, config)
            st.session_state["repair"] = repair
            if ui_service.cleanup_unconfirmed(repair):
                st.session_state["cleanup_blocked"] = True
                st.rerun()
        repair = st.session_state.get("repair")
        if repair is None:
            st.caption("Choose a task and run a repair. Independent evaluation is available afterward.")
            return
        st.subheader("Repair result")
        st.write(f"Status: {repair['status']} · Agent accepted: {repair['agent_accepted']}")
        st.caption(repair["detail"])
        st.code(repair.get("patch") or "No source change submitted.", language="diff")
        with st.expander("Candidate source"):
            candidate = repair.get("candidate")
            st.code(candidate["replacement_source"] if candidate else "No candidate.", language="python")
        with st.expander("Visible test outcomes", expanded=True):
            if "initial_execution" in repair:
                display_execution("Original", repair["initial_execution"])
            display_execution("Candidate", repair.get("repair_execution"))
        with st.expander("Attempts and generated-case decisions"):
            st.json(repair["attempt_history"])
            if "test_generation" in repair:
                st.json(repair["test_generation"])
        with st.expander("Usage and resource limits"):
            st.json(repair["usage"])
            st.json(repair["configuration"])
            st.caption("Null means unknown. Token ceilings are limits, not measured usage. API cost excludes local compute.")
        st.download_button("Download repair JSON", json.dumps(repair, indent=2, allow_nan=False),
                           file_name=f"{repair['run_id']}-repair.json", mime="application/json")
        st.subheader("Independent evaluation")
        st.caption("Separate post-repair action. Its tests and results are never sent back to the repair provider. Finite-test success is not proof.")
        if st.button("Evaluate final candidate", key="evaluate", disabled=blocked):
            with st.spinner("Scoring original and final sources independently…"):
                score = ui_service.evaluate_repair(args.data_root, repair)
            st.session_state["score"] = score
            if ui_service.cleanup_unconfirmed(score):
                st.session_state["cleanup_blocked"] = True
                st.rerun()
        score = st.session_state.get("score")
        if score:
            st.write(f"Suite passed: {score['suite_passed']} · Accepted but failed: {score['accepted_but_failed']}")
            display_execution("Original on independent suite", score["baseline_execution"])
            display_execution("Final candidate on independent suite", score["candidate_execution"])
            st.download_button("Download evaluation JSON", json.dumps(score, indent=2, allow_nan=False),
                               file_name=f"{score['evaluation_id']}-evaluation.json", mime="application/json")
    except (ValidationError, OSError) as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
