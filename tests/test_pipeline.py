from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from vericode import experiments
from vericode.datasets import load_task
from vericode.execution import MockExecutor
from vericode.experiments import run_mock_demo, write_run
from vericode.patches import candidate_workspace, validate_candidate
from vericode.providers import MockProvider, RepairRequest
from vericode.repair import repair_once_mock
from vericode.schemas import Candidate, ValidationError


@pytest.mark.parametrize("task_id", ["clamp", "sum_positive", "count_vowels"])
def test_offline_end_to_end_is_explicitly_unmeasured(data_root, tmp_path, monkeypatch, task_id):
    monkeypatch.setattr(experiments, "_git_revision", lambda: None)
    before = {path: path.read_bytes() for path in data_root.rglob("*.json")}
    record = run_mock_demo(data_root, task_id)
    path = tmp_path / f"{task_id}.json"
    write_run(path, record)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["run_kind"] == "mock"
    assert saved["provider"] == "mock"
    assert saved["repair_execution"]["status"] == "not_executed"
    assert saved["evaluation"]["suite_passed"] is None
    assert saved["evaluation"]["execution"]["status"] == "not_executed"
    assert saved["agent_accepted"] is None
    assert saved["usage"] == {
        "attempts": 1, "model_calls": 1, "input_tokens": None,
        "output_tokens": None, "cost_usd": 0.0,
    }
    assert saved["candidate"]["replacement_source"] != load_task(data_root / "repair", task_id).source
    assert "--- a/solution.py" in saved["patch"]
    assert "+++ b/solution.py" in saved["patch"]
    assert saved["configuration"]["paid_api_enabled"] is False
    assert {path: path.read_bytes() for path in before} == before


def test_evaluator_is_loaded_only_after_provider_returns(data_root, monkeypatch):
    calls = []
    original_loader = experiments.load_evaluation_suite

    class RecordingProvider(MockProvider):
        def propose(self, request):
            assert set(asdict(request)) == {"task"}
            assert set(asdict(request.task)) == {
                "schema_version", "dataset_version", "task_id", "split", "specification",
                "entry_point", "task_file", "source", "repair_tests",
            }
            assert "test_outside_bounds" not in request.prompt()
            assert str(data_root / "evaluation") not in request.prompt()
            calls.append("provider")
            return super().propose(request)

    def recording_loader(root, task_id):
        assert calls == ["provider"]
        calls.append("evaluator")
        return original_loader(root, task_id)

    monkeypatch.setattr(experiments, "MockProvider", RecordingProvider)
    monkeypatch.setattr(experiments, "load_evaluation_suite", recording_loader)
    monkeypatch.setattr(experiments, "_git_revision", lambda: None)
    record = run_mock_demo(data_root, "clamp")
    assert calls == ["provider", "evaluator"]
    assert "test_outside_bounds" not in json.dumps(record)


def test_candidate_and_tests_are_never_executed_on_host(data_root, tmp_path):
    marker = tmp_path / "must-not-exist.txt"
    payload = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
    task = replace(load_task(data_root / "repair", "clamp"), repair_tests=payload)

    class SideEffectProvider(MockProvider):
        def propose(self, request):
            response = super().propose(request)
            candidate = replace(response.candidate, replacement_source=payload + response.candidate.replacement_source)
            return replace(response, candidate=candidate)

    repair = repair_once_mock(task, SideEffectProvider())
    assert repair.execution.status == "not_executed"
    assert not marker.exists()


def test_workspace_has_only_repair_files_and_is_cleaned_on_error(data_root):
    task = load_task(data_root / "repair", "clamp")
    candidate = MockProvider().propose(RepairRequest(task)).candidate
    workspace: Path | None = None
    with pytest.raises(RuntimeError, match="test failure"):
        with candidate_workspace(task, candidate) as workspace:
            assert {path.name for path in workspace.iterdir()} == {"solution.py", "test_visible.py"}
            assert (workspace / "solution.py").read_text(encoding="utf-8") == candidate.replacement_source
            assert (workspace / "test_visible.py").read_text(encoding="utf-8") == task.repair_tests
            raise RuntimeError("test failure")
    assert workspace is not None and not workspace.exists()


def test_workspace_is_cleaned_after_success(data_root, monkeypatch):
    paths = []
    original_run = MockExecutor.run

    def recording_run(self, workspace):
        paths.append(workspace)
        return original_run(self, workspace)

    monkeypatch.setattr(MockExecutor, "run", recording_run)
    repair_once_mock(load_task(data_root / "repair", "clamp"), MockProvider())
    assert len(paths) == 1
    assert not paths[0].exists()


@pytest.mark.parametrize("task_id,source,message", [
    ("wrong_task", "def clamp(): pass", "task_id"),
    ("clamp", "def clamp(:", "parseable"),
    ("clamp", "def other_function(): pass", "top-level function"),
])
def test_bad_patch_is_rejected_before_staging(data_root, task_id, source, message):
    task = load_task(data_root / "repair", "clamp")
    with pytest.raises(ValidationError, match=message):
        validate_candidate(task, Candidate(task_id, "solution.py", source))


def test_mock_provider_rejects_final_tasks(data_root):
    task = replace(load_task(data_root / "repair", "clamp"), split="final")
    with pytest.raises(ValidationError, match="development"):
        MockProvider().propose(RepairRequest(task))


def test_logging_refuses_to_overwrite_existing_file(tmp_path):
    path = tmp_path / "run.json"
    path.write_text("keep this", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_run(path, {"run_kind": "mock"})
    assert path.read_text(encoding="utf-8") == "keep this"
