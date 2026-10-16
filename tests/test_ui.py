from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

from vericode import ui_launcher, ui_service

APP = Path(__file__).resolve().parents[1] / "src/vericode/ui.py"


def app(monkeypatch, page="Repair workbench"):
    monkeypatch.chdir(APP.parents[2])
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["provider"] = "mock"
    at.session_state["backend"] = "mock"
    at.session_state["strategy"] = "direct"
    at.run()
    if page != "Overview":
        at.button(key="nav_" + page).click().run()
    return at


def test_overview_has_feature_highlights_and_no_editor_or_configuration(monkeypatch):
    at = app(monkeypatch, "Overview")
    assert not at.exception
    assert not at.text_area and not at.text_input and not at.selectbox
    assert len([b for b in at.button if b.key and b.key.startswith("feature_")]) == 3


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
    at.selectbox(key="task_id").select("count_vowels").run()
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


def test_custom_input_requires_inference_and_api_key_entry_is_enabled(monkeypatch):
    at = app(monkeypatch)
    at.button(key="nav_Models & API").click().run()
    assert not next(field for field in at.text_input if field.label == "API key").disabled
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
    at.button(key="nav_Models & API").click().run()
    at.text_input(key="local_model_tag").set_value("my-trained-model").run()
    at.button(key="nav_Training studio").click().run()
    assert not at.exception
    at.button(key="nav_Research & reports").click().run()
    assert not at.exception
    at.button(key="nav_Repair workbench").click().run()
    assert not at.exception
    assert at.selectbox(key="task_id").value == "clamp"
    assert at.session_state["local_model_tag"] == "my-trained-model"


def test_key_verification_requires_explicit_budget_then_disconnect_forgets_key(monkeypatch, tmp_path):
    import time
    from vericode import hosted_provider, workspace_ui
    calls = []
    def verify(provider, key):
        calls.append((provider, key))
        return {"test-model": hosted_provider.Price(1, 2, hosted_provider.PRICING_URL, time.time())}
    monkeypatch.setattr(workspace_ui, "verify_connection", verify)
    real_ledger = hosted_provider.SpendLedger
    monkeypatch.setattr(workspace_ui, "SpendLedger", lambda path: real_ledger(tmp_path / "usage.sqlite3"))
    at = app(monkeypatch, "Models & API")
    at.text_input(key="api_key").set_value("test-secret-key").run()
    at.button(key="verify_key").click().run()
    assert not at.exception and calls == [("openai", "test-secret-key")]
    assert at.button(key="connect_model").disabled
    at.number_input(key="api_limit").set_value(1.0).run()
    assert at.button(key="connect_model").disabled
    at.checkbox(key="authorize_api").check().run()
    at.button(key="connect_model").click().run()
    assert not at.exception
    assert "test-secret-key" not in repr(at.session_state["hosted_connection"])
    at.button(key="nav_Repair workbench").click().run()
    at.selectbox(key="provider").select("openai").run()
    assert not at.exception
    at.button(key="nav_Usage & cost").click().run()
    assert not at.exception
    at.button(key="nav_Models & API").click().run()
    assert at.text_input(key="api_key").value == "test-secret-key"
    at.button(key="disconnect_model").click().run()
    assert not at.exception
    assert at.text_input(key="api_key").value == ""
    assert "hosted_connection" not in at.session_state
    at.button(key="nav_Deployment").click().run()
    assert not at.exception
