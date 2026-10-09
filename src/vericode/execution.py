"""Execution adapter for Day 1. It deliberately runs no code."""

from pathlib import Path

from vericode.results import ExecutionResult


class MockExecutor:
    def run(self, workspace: Path) -> ExecutionResult:
        # Even syntactically valid Python can have arbitrary side effects.
        # Do not import, eval, exec, or launch candidate/test code here.
        if not (workspace / "solution.py").is_file() or not (workspace / "test_visible.py").is_file():
            raise ValueError("mock workspace is missing candidate or visible-test text")
        return ExecutionResult(
            mode="mock", status="not_executed",
            detail="MOCK: workspace staged; candidate and visible tests were not executed.",
        )
