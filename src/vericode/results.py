"""Observed results distinguish simulation, test failure, and infrastructure errors."""

from dataclasses import dataclass
import math

from vericode.schemas import ValidationError, require_id, require_text


@dataclass(frozen=True)
class ExecutionResult:
    mode: str
    status: str
    tests_passed: int | None = None
    tests_failed: int | None = None
    duration_seconds: float | None = None
    detail: str = "No candidate code was executed."
    tests_errors: int | None = None
    tests_skipped: int | None = None
    output: str = ""
    output_truncated: bool = False
    exit_code: int | None = None
    cleanup_confirmed: bool | None = None
    job_name: str | None = None
    image_id: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("mock", "sandbox"):
            raise ValidationError("execution mode: expected 'mock' or 'sandbox'")
        if self.status not in (
            "not_executed", "passed", "failed", "test_error", "timeout",
            "output_limit", "resource_limit", "infrastructure_error"
        ):
            raise ValidationError("execution status: unsupported value")
        for field in ("tests_passed", "tests_failed", "tests_errors", "tests_skipped"):
            value = getattr(self, field)
            if value is not None and (type(value) is not int or value < 0):
                raise ValidationError(f"{field}: expected null or a non-negative integer")
        if self.duration_seconds is not None and (
            type(self.duration_seconds) not in (int, float)
            or not math.isfinite(self.duration_seconds)
            or self.duration_seconds < 0
        ):
            raise ValidationError("duration_seconds: expected null or a finite non-negative number")
        if self.mode == "mock" and (
            self.status != "not_executed"
            or self.tests_passed is not None
            or self.tests_failed is not None
            or self.duration_seconds is not None
            or self.tests_errors is not None or self.tests_skipped is not None
            or self.exit_code is not None
        ):
            raise ValidationError("mock execution cannot report measured test outcomes or timing")
        if self.status == "passed" and (
            self.tests_passed is None or self.tests_passed < 1 or self.tests_failed != 0
        ):
            raise ValidationError("passed execution requires at least one pass and zero failures")
        if self.status == "failed" and (
            self.tests_failed is None or self.tests_failed < 1
        ):
            raise ValidationError("failed execution requires at least one test failure")
        require_text(self.detail, "detail")
        if not isinstance(self.output, str) or len(self.output.encode("utf-8")) > 65_536:
            raise ValidationError("output: expected a string bounded to 65536 UTF-8 bytes")
        if type(self.output_truncated) is not bool:
            raise ValidationError("output_truncated: expected boolean")
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise ValidationError("exit_code: expected null or integer")
        if self.cleanup_confirmed is not None and type(self.cleanup_confirmed) is not bool:
            raise ValidationError("cleanup_confirmed: expected null or boolean")


@dataclass(frozen=True)
class EvaluationResult:
    task_id: str
    execution: ExecutionResult
    suite_passed: bool | None

    def __post_init__(self) -> None:
        require_id(self.task_id)
        if not isinstance(self.execution, ExecutionResult):
            raise ValidationError("evaluation execution: expected ExecutionResult")
        expected = {"passed": True, "failed": False}.get(self.execution.status)
        if self.suite_passed is not expected:
            raise ValidationError("suite_passed must agree with execution status; unknown is null")
