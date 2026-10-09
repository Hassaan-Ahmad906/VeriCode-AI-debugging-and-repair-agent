import pytest

from vericode.results import EvaluationResult, ExecutionResult
from vericode.schemas import Candidate, ValidationError


@pytest.mark.parametrize("target", ["../solution.py", "test_eval.py", "/solution.py", "C:\\solution.py", "solution.py:stream"])
def test_candidate_cannot_target_other_files(target):
    with pytest.raises(ValidationError, match="target_file"):
        Candidate("clamp", target, "def clamp(): pass")


def test_mock_cannot_claim_measured_success():
    with pytest.raises(ValidationError, match="mock execution"):
        ExecutionResult("mock", "passed", tests_passed=2, tests_failed=0)
    execution = ExecutionResult("mock", "not_executed")
    assert EvaluationResult("clamp", execution, None).suite_passed is None
    with pytest.raises(ValidationError, match="suite_passed"):
        EvaluationResult("clamp", execution, True)


def test_real_success_requires_evidence_and_consistent_evaluation():
    with pytest.raises(ValidationError, match="at least one"):
        ExecutionResult("sandbox", "passed", tests_passed=0, tests_failed=0)
    failed = ExecutionResult("sandbox", "failed", tests_passed=1, tests_failed=1)
    assert EvaluationResult("clamp", failed, False).suite_passed is False
    with pytest.raises(ValidationError, match="suite_passed"):
        EvaluationResult("clamp", failed, True)


@pytest.mark.parametrize("duration", [-1, float("nan"), float("inf"), True])
def test_invalid_duration_is_rejected(duration):
    with pytest.raises(ValidationError, match="duration_seconds"):
        ExecutionResult("sandbox", "timeout", duration_seconds=duration)
