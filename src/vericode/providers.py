"""Small provider-neutral contract with an offline, scripted implementation."""

from dataclasses import asdict
import json

from vericode.model_calls import RawCompletion, StructuredProvider
# Re-export the existing provider API to preserve Day 1/2 callers.
from vericode.model_io import (
    GenerationLimits, INSTRUCTION, ModelProvider, ModelResponse, PROMPT_VERSION, RepairRequest, Usage,
)
from vericode.schemas import Candidate, ValidationError


# Demonstration responses are controller configuration, never agent inputs or
# independent correctness evidence. No evaluator/reference files are consulted.
_SCRIPTED_REPLACEMENTS = {
    "sum_positive": "def sum_positive(values):\n    return sum(value for value in values if value > 0)\n",
    "count_vowels": "def count_vowels(text):\n    return sum(char in 'aeiouAEIOU' for char in text)\n",
    "clamp": "def clamp(value, lower, upper):\n    return max(lower, min(value, upper))\n",
}


class MockTransport:
    offline = True

    def complete(self, prompt: str, *, model: str, max_output_tokens: int,
                 timeout_seconds: float) -> RawCompletion:
        task_id = json.loads(prompt.split("\n\n", 1)[1])["task_id"]
        candidate = Candidate(task_id, "solution.py", _SCRIPTED_REPLACEMENTS[task_id])
        return RawCompletion(json.dumps(asdict(candidate)), Usage(cost_usd=0.0), model)


class MockProvider(StructuredProvider):
    """One deterministic canned response per known development fixture."""

    def __init__(self, model: str = "scripted-v1", limits: GenerationLimits | None = None):
        super().__init__(MockTransport(), provider="mock", model=model, limits=limits)

    def propose(self, request: RepairRequest) -> ModelResponse:
        task = request.task
        if task.split != "development" or task.dataset_version != "self-authored-v1":
            raise ValidationError("mock provider supports only self-authored-v1 development tasks")
        if task.task_id not in _SCRIPTED_REPLACEMENTS:
            raise ValidationError(f"mock provider has no scripted response for {task.task_id!r}")
        return super().propose(request)
