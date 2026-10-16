"""Strategy C: independently checked test proposals followed by bounded B."""

from dataclasses import asdict, replace
import hashlib
from pathlib import Path
from time import monotonic

from vericode.datasets import TaskManifest
from vericode.direct_run import make_executor
from vericode.feedback import FeedbackOutcome, feedback_repair
from vericode.feedback_run import record_feedback_outcome
from vericode.generated_tests import (
    ORACLE_VERSION, TEST_PROMPT_VERSION, TestGenerationRequest, make_test_provider, parse_cases, validate_cases,
)
from vericode.model_calls import ProviderFailure, provider_enabled
from vericode.model_io import summarize_calls
from vericode.providers import make_provider
from vericode.run_config import AugmentedConfiguration
from vericode.schemas import ValidationError


def record_augmented_task(task, config: AugmentedConfiguration, executor=None, *, generator=None, repair_provider=None):
    started = monotonic()
    generator = generator if generator is not None else (make_provider(config) if config.provider != "mock" else make_test_provider(config.model, config.generation))
    repair_provider = repair_provider if repair_provider is not None else make_provider(config)
    request = TestGenerationRequest(task)
    decisions = []
    generated_calls = ()
    tests = task.repair_tests
    failure = None
    if not provider_enabled(generator) or not provider_enabled(repair_provider):
        failure = ("paid_execution_disabled", "Only offline providers are enabled.")
    else:
        try:
            reply = generator.generate(request, parse_cases,
                                       max_transport_calls=min(config.feedback.max_model_calls, generator.limits.max_transport_calls))
            generated_calls = reply.calls
            tests, decisions = validate_cases(task, reply.value)
        except ProviderFailure as exc:
            generated_calls = exc.calls
            failure = (exc.code, str(exc))
    remaining = config.feedback.max_model_calls - len(generated_calls)
    if failure is None and remaining <= 0:
        failure = ("model_call_budget_exhausted", "Test generation consumed the shared model-call budget.")
    if failure:
        outcome = FeedbackOutcome(*failure, generated_calls, None, None, None, None, None, (), monotonic() - started)
    else:
        augmented = replace(task, repair_tests=tests)
        outcome = feedback_repair(augmented, repair_provider, executor if executor is not None else make_executor(config),
                                  replace(config.feedback, max_model_calls=remaining))
        offset = len(generated_calls)
        outcome = replace(outcome,
                          calls=generated_calls + tuple(replace(call, call_index=call.call_index + offset) for call in outcome.calls),
                          history=tuple(replace(attempt, call_indices=tuple(i + offset for i in attempt.call_indices))
                                        for attempt in outcome.history), duration_seconds=monotonic() - started)
    record = record_feedback_outcome(task, config, outcome)
    record["test_generation"] = {"prompt_version": TEST_PROMPT_VERSION, "prompt": request.prompt(),
                                 "oracle_version": ORACLE_VERSION, "decisions": decisions,
                                 "accepted": sum(d["accepted"] for d in decisions),
                                 "discarded": sum(not d["accepted"] for d in decisions),
                                 "usage": summarize_calls(generated_calls)}
    record["augmented_tests_sha256"] = hashlib.sha256(tests.encode("utf-8")).hexdigest()
    generation_count = len(generated_calls)
    for index, call in enumerate(record["model_calls"]):
        call["purpose"] = "test_generation" if index < generation_count else "repair"
    record["usage"]["repair_responses"] = sum(call.status in ("completed", "invalid_response")
                                               for call in outcome.calls[generation_count:])
    record["usage"]["test_generation_responses"] = sum(call.status in ("completed", "invalid_response") for call in generated_calls)
    record["limitations"].append("Generated expectations are accepted only within reviewed specification-rule domains; invalid cases are discarded.")
    return record


def run_augmented(data_root: Path, task_id: str, config: AugmentedConfiguration):
    manifest = TaskManifest.load(data_root / "manifests/development.json")
    tasks = {task.task_id: task for task in manifest.load_tasks(data_root / "repair")}
    if manifest.split != "development" or task_id not in tasks:
        raise ValidationError(f"{task_id!r}: not listed in the development manifest")
    return record_augmented_task(tasks[task_id], config)
