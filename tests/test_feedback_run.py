from dataclasses import replace
import json
import shutil

import pytest

from vericode import batch
from vericode.cli import main
from vericode.feedback import FeedbackLimits
from vericode.feedback_run import run_feedback
from vericode.run_config import FeedbackConfiguration, RunConfiguration
from vericode.schemas import ValidationError


def test_feedback_config_roundtrip_preserves_direct_schema():
    direct = RunConfiguration()
    feedback = FeedbackConfiguration()
    assert direct.to_dict()["schema_version"] == 1 and "feedback" not in direct.to_dict()
    assert feedback.to_dict()["schema_version"] == 2
    assert RunConfiguration.from_dict(feedback.to_dict()) == feedback
    changed = feedback.to_dict()
    changed["schema_version"] = 1
    with pytest.raises(ValidationError, match="schema_version 2"):
        RunConfiguration.from_dict(changed)


def test_feedback_cli_saves_complete_mock_history(data_root, tmp_path, capsys):
    output = tmp_path / "run.json"
    assert main(["feedback", "--data-root", str(data_root), "--output", str(output)]) == 0
    record = json.loads(capsys.readouterr().out)
    assert json.loads(output.read_text()) == record
    assert record["strategy"] == "feedback" and record["schema_version"] == 2
    assert record["status"] == "candidate_ready" and record["agent_accepted"] is None
    assert record["evaluation"] is None and record["paid_api_enabled"] is False
    assert record["usage"]["attempts"] == record["usage"]["model_calls"] == 1
    assert record["usage"]["cost_usd"] == 0
    assert record["initial_execution"]["status"] == "not_executed"
    assert len(record["attempt_history"]) == 1
    assert record["attempt_history"][0]["call_indices"] == [1]


def test_feedback_run_needs_no_evaluator_tree(data_root, tmp_path):
    shutil.copytree(data_root / "repair", tmp_path / "repair")
    shutil.copytree(data_root / "manifests", tmp_path / "manifests")
    record = run_feedback(tmp_path, "clamp", FeedbackConfiguration())
    assert record["evaluation"] is None and record["status"] == "candidate_ready"
    assert "evaluation" not in record["attempt_history"][0]["prompt"]


def test_feedback_batch_resume_adds_no_calls_and_rejects_changed_limits(data_root, tmp_path, monkeypatch):
    config = FeedbackConfiguration()
    directory = tmp_path / "batch"
    first = batch.run_batch(data_root, data_root / "manifests/development.json", config, directory)
    before = (directory / "events.jsonl").read_bytes()
    monkeypatch.setattr(batch, "record_feedback_task", lambda *a, **kw: pytest.fail("completed outcomes must be skipped"))
    second = batch.run_batch(data_root, data_root / "manifests/development.json", config, directory, resume=True)
    assert first["completed"] == second["completed"] == 3
    assert second["newly_completed"] == 0 and second["skipped_completed"] == 3
    assert second["usage"]["model_calls"] == 3
    assert (directory / "events.jsonl").read_bytes() == before
    changed = replace(config, feedback=FeedbackLimits(max_attempts=2))
    with pytest.raises(ValidationError, match="changed"):
        batch.run_batch(data_root, data_root / "manifests/development.json", changed, directory, resume=True)
