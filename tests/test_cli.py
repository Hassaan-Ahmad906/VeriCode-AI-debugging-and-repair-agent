import json

import pytest

from vericode import experiments
from vericode.cli import main


def test_cli_demo_saves_parseable_mock_json(data_root, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(experiments, "_git_revision", lambda: None)
    output = tmp_path / "demo.json"
    assert main(["demo", "--data-root", str(data_root), "--output", str(output)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == json.loads(output.read_text(encoding="utf-8"))
    assert printed["run_kind"] == "mock"
    assert printed["evaluation"]["suite_passed"] is None


def test_cli_lists_validated_tasks(data_root, capsys):
    assert main(["list-tasks", "--data-root", str(data_root)]) == 0
    output = capsys.readouterr().out
    assert all(task_id in output for task_id in ("clamp", "sum_positive", "count_vowels"))


def test_cli_unknown_task_has_actionable_error(data_root, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["demo", "--task", "missing", "--data-root", str(data_root)])
    assert exc.value.code == 2
    output = capsys.readouterr()
    assert "not listed in the development manifest" in output.err
    assert "Traceback" not in output.err


def test_cli_does_not_enable_live_provider_from_environment(data_root, capsys, monkeypatch):
    monkeypatch.setenv("VERICODE_PROVIDER", "live-provider-not-implemented")
    monkeypatch.setenv("VERICODE_SPENDING_CAP_USD", "100")
    monkeypatch.setenv("VERICODE_API_KEY", "sentinel-do-not-log")
    monkeypatch.setattr(experiments, "_git_revision", lambda: None)
    main(["demo", "--data-root", str(data_root)])
    output = capsys.readouterr().out
    assert "sentinel-do-not-log" not in output
    assert json.loads(output)["provider"] == "mock"


def test_cli_visible_check_defaults_to_mock(data_root, capsys, monkeypatch):
    monkeypatch.setattr("vericode.jobs._git_revision", lambda: None)
    assert main(["run-tests", "--data-root", str(data_root)]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["execution"]["status"] == "not_executed"
    assert record["configuration"]["backend"] == "mock"
    assert record["evaluation"] is None


def test_existing_output_is_rejected_before_job_starts(tmp_path, monkeypatch, capsys):
    output = tmp_path / "existing.json"
    output.write_text("preserve", encoding="utf-8")

    def forbidden(*args, **kwargs):
        pytest.fail("existing output must be detected before executing a job")

    monkeypatch.setattr("vericode.cli.run_visible_check", forbidden)
    with pytest.raises(SystemExit) as exc:
        main(["run-tests", "--output", str(output)])
    assert exc.value.code == 2
    assert "already exists" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == "preserve"


@pytest.mark.parametrize("status,expected", [("passed", 0), ("failed", 1), ("timeout", 1), ("infrastructure_error", 2)])
def test_cli_exit_code_distinguishes_test_outcomes_and_infrastructure(status, expected, monkeypatch, capsys):
    monkeypatch.setattr("vericode.cli.run_visible_check", lambda *args, **kwargs: {"execution": {"status": status}})
    assert main(["run-tests", "--backend", "docker"]) == expected
    assert json.loads(capsys.readouterr().out)["execution"]["status"] == status
