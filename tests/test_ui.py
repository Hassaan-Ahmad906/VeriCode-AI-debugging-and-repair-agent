from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

from vericode import ui_launcher, ui_service

APP = Path(__file__).resolve().parents[1] / "src/vericode/ui.py"


def app(monkeypatch):
    monkeypatch.chdir(APP.parents[2])
    return AppTest.from_file(str(APP), default_timeout=30).run()


def test_repair_evaluation_are_separate_and_selection_discards_stale_result(monkeypatch):
    at = app(monkeypatch)
    assert not at.exception
    at.button(key="run_repair").click().run()
    repair_id = at.session_state["repair"]["run_id"]
    assert "score" not in at.session_state
    assert at.session_state["repair"]["evaluation"] is None
    at.button(key="evaluate").click().run()
    assert not at.exception
    assert at.session_state["score"]["repair_run_id"] == repair_id
    assert at.session_state["score"]["suite_passed"] is None
    at.selectbox(key="task_id").select("clamp").run()
    assert "repair" not in at.session_state and "score" not in at.session_state


@pytest.mark.parametrize("strategy", ["feedback", "augmented"])
def test_ui_uses_shared_controllers_without_host_execution(monkeypatch, strategy):
    def forbidden(*args, **kwargs):
        raise AssertionError("repair must not load evaluation suites")
    monkeypatch.setattr(ui_service, "score_record", forbidden)
    at = app(monkeypatch)
    at.selectbox(key="strategy").select(strategy).run()
    at.button(key="run_repair").click().run()
    assert not at.exception
    record = at.session_state["repair"]
    assert record["strategy"] == strategy
    assert record["repair_execution"]["status"] == "not_executed"
    assert record["paid_api_enabled"] is False


def test_launcher_cannot_bind_publicly(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ui_launcher.subprocess, "call", lambda args: calls.append(args) or 0)
    assert ui_launcher.main(["--data-root", str(tmp_path)]) == 0
    assert "--server.address=127.0.0.1" in calls[0]
    assert "--browser.gatherUsageStats=false" in calls[0]
    with pytest.raises(SystemExit):
        ui_launcher.main(["--server.address", "0.0.0.0"])


def test_unconfirmed_cleanup_blocks_next_ui_job(monkeypatch):
    real = ui_service.repair_task
    def uncertain(task, config):
        result = real(task, config)
        result["repair_execution"]["cleanup_confirmed"] = False
        return result
    monkeypatch.setattr(ui_service, "repair_task", uncertain)
    at = app(monkeypatch)
    at.button(key="run_repair").click().run()
    assert not at.exception
    assert at.button(key="run_repair").disabled
    assert at.button(key="evaluate").disabled


def test_custom_input_requires_real_local_provider_and_api_keys_are_disabled(monkeypatch):
    at = app(monkeypatch)
    at.button(key="nav_Model settings").click().run()
    assert next(field for field in at.text_input if field.label == "API key").disabled
    at.button(key="nav_Repair workbench").click().run()
    at.selectbox(key="input_mode").select("custom function").run()
    assert at.warning
    at.button(key="run_repair").click().run()
    assert "repair" not in at.session_state


def test_workspace_navigation_preserves_configuration_and_history(monkeypatch):
    at = app(monkeypatch)
    at.selectbox(key="task_id").select("clamp").run()
    at.button(key="run_repair").click().run()
    at.button(key="nav_Run history").click().run()
    assert not at.exception and len(at.session_state["run_history"]) == 1
    at.button(key="nav_Model settings").click().run()
    at.text_input(key="local_model_tag").set_value("my-trained-model").run()
    at.button(key="nav_Training studio").click().run()
    assert not at.exception
    at.button(key="nav_Research & reports").click().run()
    assert not at.exception
    at.button(key="nav_Repair workbench").click().run()
    assert not at.exception
    assert at.selectbox(key="task_id").value == "clamp"
    assert at.text_input(key="local_model_tag").value == "my-trained-model"
