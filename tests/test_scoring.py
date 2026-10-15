from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from vericode.cli import main
from vericode.datasets import load_task
from vericode.direct_run import record_direct_task
from vericode.feedback_run import record_feedback_task
from vericode.jobs import MockJobExecutor
from vericode.results import ExecutionResult
from vericode.run_config import FeedbackConfiguration, RunConfiguration
from vericode.schemas import ValidationError
from vericode.scoring import score_record
from vericode.metrics import evaluation_metrics
from vericode.records import read_record
from test_feedback import FAILED, PASSED, ScriptedExecutor


def test_score_does_not_mutate_repair_and_receives_only_evaluator_contents(data_root):
    task = load_task(data_root / "repair", "sum_positive")
    repair = record_feedback_task(task, FeedbackConfiguration(), ScriptedExecutor([PASSED]))
    before = deepcopy(repair)
    executor = ScriptedExecutor([FAILED, FAILED])
    score = score_record(data_root, repair, RunConfiguration(), executor)
    assert repair == before and repair["evaluation"] is None
    assert score["suite_passed"] is False and score["accepted_but_failed"] is True
    assert score["baseline_suite_passed"] is False and score["regression"] is False
    assert score["model_calls"] == 0 and score["api_cost_usd"] == 0
    assert executor.jobs[0][1] != task.repair_tests and executor.jobs[0][1] == executor.jobs[1][1]


def test_regression_uses_measured_original_baseline(data_root):
    task = load_task(data_root / "repair", "clamp")
    repair = record_direct_task(task, RunConfiguration())
    score = score_record(data_root, repair, RunConfiguration(), ScriptedExecutor([PASSED, FAILED]))
    assert score["regression"] is True and score["suite_passed"] is False


def test_timeout_remains_unknown_and_unconfirmed_cleanup_stops_candidate(data_root):
    repair = record_direct_task(load_task(data_root / "repair", "clamp"), RunConfiguration())
    timeout = ExecutionResult("sandbox", "timeout", cleanup_confirmed=True)
    score = score_record(data_root, repair, RunConfiguration(), ScriptedExecutor([FAILED, timeout]))
    assert score["suite_passed"] is None and score["regression"] is None
    uncertain = replace(PASSED, cleanup_confirmed=False)
    executor = ScriptedExecutor([uncertain])
    score = score_record(data_root, repair, RunConfiguration(), executor)
    assert score["status"] == "infrastructure_error" and score["candidate_execution"] is None
    assert score["baseline_suite_passed"] is None and len(executor.jobs) == 1


@pytest.mark.parametrize("change", ["task_id", "source_sha256", "visible_tests_sha256", "dataset_version", "candidate"])
def test_mismatched_repair_is_rejected_before_evaluator_execution(data_root, change):
    repair = record_direct_task(load_task(data_root / "repair", "clamp"), RunConfiguration())
    repair[change] = {"task_id": "clamp", "target_file": "../evaluation.py", "replacement_source": "def clamp(): pass"} if change == "candidate" else "wrong"
    executor = ScriptedExecutor([])
    with pytest.raises(ValidationError):
        score_record(data_root, repair, RunConfiguration(), executor)
    assert not executor.jobs


def test_mock_evaluator_cannot_report_passes_and_cli_preserves_input(data_root, tmp_path, capsys):
    repair = record_direct_task(load_task(data_root / "repair", "clamp"), RunConfiguration())
    path = tmp_path / "repair.json"
    path.write_text(json.dumps(repair))
    before = path.read_bytes()
    assert main(["evaluate", "--record", str(path), "--data-root", str(data_root)]) == 0
    score = json.loads(capsys.readouterr().out)
    assert score["run_kind"] == "mock" and score["suite_passed"] is None
    assert score["baseline_suite_passed"] is None and path.read_bytes() == before


def test_metrics_keep_unresolved_outcomes_and_explicit_denominators(data_root):
    repair = record_direct_task(load_task(data_root / "repair", "clamp"), RunConfiguration())
    known = score_record(data_root, repair, RunConfiguration(), ScriptedExecutor([PASSED, FAILED]))
    unknown = score_record(data_root, repair, RunConfiguration(), MockJobExecutor())
    summary = evaluation_metrics([known, unknown])
    assert summary["tasks"] == 2 and summary["evaluation_unknown"] == 1
    assert summary["evaluation_pass_fraction"] is None
    assert summary["observed_pass_lower_bound"] == 0 and summary["observed_pass_upper_bound"] == 0.5
    assert summary["regressions"] == 1 and summary["regression_fraction"] == 1
    assert evaluation_metrics([])["evaluation_pass_fraction"] is None


def test_record_reader_accepts_real_history_sizes_and_rejects_duplicate_json(tmp_path):
    path = tmp_path / "large.json"
    path.write_text(json.dumps({"history": "x" * 100000}))
    assert len(read_record(path)["history"]) == 100000
    path.write_text('{"field":1,"field":2}')
    with pytest.raises(ValidationError):
        read_record(path)


def test_logged_invalid_patch_is_not_executed_or_silently_repaired(data_root):
    repair = record_direct_task(load_task(data_root / "repair", "clamp"), RunConfiguration())
    repair["status"] = "invalid_patch"
    repair["candidate"]["replacement_source"] = "def other(): pass\n"
    executor = ScriptedExecutor([FAILED])
    score = score_record(data_root, repair, RunConfiguration(), executor)
    assert score["status"] == "no_candidate" and score["rejected_candidate"] is True
    assert score["suite_passed"] is None and len(executor.jobs) == 1


@pytest.mark.docker
def test_overfit_visible_success_fails_independent_suite(data_root, docker_executor):
    task = load_task(data_root / "repair", "sum_positive")
    repair = record_feedback_task(task, FeedbackConfiguration(backend="docker"), docker_executor)
    assert repair["agent_accepted"] is True and repair["usage"]["model_calls"] == 0
    score = score_record(data_root, repair, RunConfiguration(backend="docker"), docker_executor)
    assert score["suite_passed"] is False, score
    assert score["accepted_but_failed"] is True and score["regression"] is False
    assert score["candidate_execution"]["cleanup_confirmed"] is True
    assert repair["evaluation"] is None


@pytest.mark.docker
def test_scripted_repair_passes_independent_development_suite(data_root, docker_executor):
    task = load_task(data_root / "repair", "clamp")
    repair = record_direct_task(task, RunConfiguration(backend="docker"), docker_executor)
    score = score_record(data_root, repair, RunConfiguration(backend="docker"), docker_executor)
    assert score["baseline_suite_passed"] is False and score["suite_passed"] is True, score
    assert score["candidate_execution"]["cleanup_confirmed"] is True
