from dataclasses import replace
import json

import pytest

from vericode.augmented import record_augmented_task
from vericode.cli import main
from vericode.datasets import load_task
from vericode.generated_tests import parse_cases, validate_cases
from vericode.jobs import MockJobExecutor
from vericode.model_calls import RawCompletion, StructuredProvider, TransientTransportError
from vericode.model_io import Usage
from vericode.run_config import AugmentedConfiguration, RunConfiguration
from vericode.feedback import FeedbackLimits
from test_feedback import FAILED, PASSED, ScriptedExecutor, ScriptedTransport


def test_wrong_expectations_duplicates_and_code_injection_are_discarded(data_root):
    task = load_task(data_root / "repair", "sum_positive")
    cases = [
        {"args": [[-2, 4]], "expected": 2},  # buggy code's answer is not trusted
        {"args": [[-2, 4]], "expected": 4},
        {"args": [[-2, 4]], "expected": 4},
        {"args": ["__import__('os').system('unsafe')"], "expected": 0},
        {"args": [[1]], "expected": True},
        {"args": [[1]], "expected": 1, "code": "unsafe"},
    ]
    tests, decisions = validate_cases(task, cases)
    assert [d["accepted"] for d in decisions] == [False, True, False, False, False, False]
    assert tests.startswith(task.repair_tests)
    assert "unsafe" not in tests and "[-2, 4]" in tests
    assert all(d["rendered_test"] is None for d in decisions if not d["accepted"])


def test_cannot_shadow_a_visible_test(data_root):
    task = replace(load_task(data_root / "repair", "clamp"),
                   repair_tests="def test_vericode_generated_0 ( ):\n    assert False\n")
    tests, decisions = validate_cases(task, [{"args": [1, 0, 5], "expected": 1}])
    assert tests == task.repair_tests and not decisions[0]["accepted"]


@pytest.mark.parametrize("text", ['{}', '{"cases":[]}', '{"cases":[NaN]}', '{"cases":[],"cases":[]}'])
def test_invalid_generation_response_is_rejected(text):
    with pytest.raises(ValueError):
        parse_cases(text, 65536)


def test_augmented_mock_records_generation_and_repair_calls_separately(data_root):
    task = load_task(data_root / "repair", "sum_positive")
    record = record_augmented_task(task, AugmentedConfiguration(), MockJobExecutor())
    assert record["schema_version"] == 3 and record["status"] == "candidate_ready"
    assert record["test_generation"]["accepted"] == 1 and record["test_generation"]["discarded"] == 0
    assert record["usage"]["model_calls"] == 2 and record["usage"]["repair_responses"] == 1
    assert [c["purpose"] for c in record["model_calls"]] == ["test_generation", "repair"]
    assert [c["call_index"] for c in record["model_calls"]] == [1, 2]
    assert record["attempt_history"][0]["call_indices"] == (2,)
    assert record["evaluation"] is None and record["agent_accepted"] is None
    assert record["augmented_tests_sha256"] != record["visible_tests_sha256"]


def test_generation_cannot_consume_an_extra_repair_call(data_root):
    task = load_task(data_root / "repair", "clamp")
    executor = ScriptedExecutor([])
    record = record_augmented_task(task, AugmentedConfiguration(feedback=FeedbackLimits(max_model_calls=1)), executor)
    assert record["status"] == "model_call_budget_exhausted" and record["usage"]["model_calls"] == 1
    assert record["usage"]["attempts"] == 0 and not executor.jobs


def test_invalid_test_response_logs_usage_and_never_executes(data_root):
    transport = ScriptedTransport([TransientTransportError("unknown"), RawCompletion('{bad', Usage(8, 4, 0.0))])
    generator = StructuredProvider(transport, provider="test_mock", model="mock")
    executor = ScriptedExecutor([])
    record = record_augmented_task(load_task(data_root / "repair", "clamp"), AugmentedConfiguration(), executor, generator=generator)
    assert record["status"] == "invalid_response" and record["usage"]["model_calls"] == 2
    assert record["usage"]["cost_usd"] is None and not executor.jobs


def test_all_invalid_generated_cases_are_logged_and_b_runs_on_original_tests(data_root):
    task = load_task(data_root / "repair", "sum_positive")
    transport = ScriptedTransport([RawCompletion(json.dumps({"cases": [{"args": [[-2, 4]], "expected": 2}]}), Usage(cost_usd=0.0))])
    executor = ScriptedExecutor([PASSED])
    record = record_augmented_task(task, AugmentedConfiguration(), executor,
                                   generator=StructuredProvider(transport, provider="test_mock", model="mock"))
    assert record["test_generation"]["accepted"] == 0 and record["test_generation"]["discarded"] == 1
    assert record["status"] == "visible_passed" and record["usage"]["model_calls"] == 1
    assert executor.jobs[0][1] == task.repair_tests


def test_augmented_configuration_and_cli(data_root, capsys):
    config = AugmentedConfiguration()
    assert RunConfiguration.from_dict(config.to_dict()) == config
    assert main(["augment", "--data-root", str(data_root)]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["strategy"] == "augmented" and record["usage"]["model_calls"] == 2


@pytest.mark.docker
def test_generated_case_reveals_weak_visible_suite_and_repair_passes(data_root, docker_executor):
    task = load_task(data_root / "repair", "sum_positive")
    record = record_augmented_task(task, AugmentedConfiguration(backend="docker"), docker_executor)
    assert record["status"] == "visible_passed", record["detail"]
    assert record["initial_execution"]["status"] == "failed"
    assert record["repair_execution"]["tests_passed"] == 3
    assert record["repair_execution"]["cleanup_confirmed"] is True
    assert record["usage"]["model_calls"] == 2 and record["evaluation"] is None
