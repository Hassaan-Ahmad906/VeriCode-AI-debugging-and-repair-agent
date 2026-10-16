"""Strategy A: one repair response, followed by observation without revision."""

from dataclasses import dataclass
from time import monotonic

from vericode.jobs import CandidateExecutor, VisibleJob
from vericode.model_calls import ProviderFailure, provider_enabled
from vericode.model_io import CallRecord, ModelProvider, RepairRequest
from vericode.patches import preview_diff
from vericode.results import ExecutionResult
from vericode.schemas import Candidate, RepairTask, ValidationError


@dataclass(frozen=True)
class DirectOutcome:
    status: str
    detail: str
    calls: tuple[CallRecord, ...]
    candidate: Candidate | None
    patch: str | None
    execution: ExecutionResult | None
    agent_accepted: bool | None
    duration_seconds: float


def direct_repair(task: RepairTask, provider: ModelProvider, executor: CandidateExecutor) -> DirectOutcome:
    started = monotonic()
    # Both the strategy and standard adapter guard against accidental paid calls.
    if not provider_enabled(provider):
        return DirectOutcome("paid_execution_disabled", "Only offline providers are enabled.", (), None, None, None, None, monotonic() - started)
    try:
        response = provider.propose(RepairRequest(task))
    except ProviderFailure as exc:
        accepted = False if exc.code == "invalid_response" else None
        return DirectOutcome(exc.code, str(exc), exc.calls, None, None, None, accepted, monotonic() - started)
    except ValidationError as exc:
        # Mock fixture restrictions are checked before any transport invocation.
        return DirectOutcome("invalid_task", str(exc), (), None, None, None, None, monotonic() - started)
    # No execution occurs before the provider returns. It never receives these outcomes.
    try:
        patch = preview_diff(task, response.candidate)
        job = VisibleJob.from_task(task, response.candidate)
    except ValidationError as exc:
        return DirectOutcome("invalid_patch", str(exc), response.calls, response.candidate, None, None, False, monotonic() - started)
    try:
        execution = job.execute(executor)
    except Exception:
        return DirectOutcome("infrastructure_error", "Execution adapter failed; candidate retained and no retry attempted.",
                             response.calls, response.candidate, patch, None, None, monotonic() - started)
    accepted = {"passed": True, "failed": False, "test_error": False}.get(execution.status)
    status = {"passed": "visible_passed", "failed": "visible_failed", "not_executed": "candidate_ready"}.get(execution.status, execution.status)
    return DirectOutcome(status, execution.detail, response.calls, response.candidate, patch, execution,
                         accepted, monotonic() - started)
