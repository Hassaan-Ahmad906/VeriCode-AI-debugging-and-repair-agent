"""One-shot mock demonstration; real strategies A/B/C are later-session work."""

from dataclasses import dataclass

from vericode.execution import MockExecutor
from vericode.patches import candidate_workspace, preview_diff
from vericode.providers import ModelProvider, ModelResponse, RepairRequest
from vericode.results import ExecutionResult
from vericode.schemas import RepairTask


@dataclass(frozen=True)
class RepairOutcome:
    response: ModelResponse
    patch: str
    execution: ExecutionResult
    prompt: str
    attempts: int = 1
    model_calls: int = 1


def repair_once_mock(task: RepairTask, provider: ModelProvider) -> RepairOutcome:
    # This function has no evaluator argument, path, or final-test feedback.
    request = RepairRequest(task)
    response = provider.propose(request)
    patch = preview_diff(task, response.candidate)
    with candidate_workspace(task, response.candidate) as workspace:
        execution = MockExecutor().run(workspace)
    return RepairOutcome(response, patch, execution, request.prompt())
