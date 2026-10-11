from dataclasses import asdict, replace
import shutil

import pytest

from vericode.datasets import load_task
from vericode.jobs import VisibleJob, run_visible_check
from vericode.providers import MockProvider, RepairRequest
from vericode.schemas import Candidate, ValidationError


def test_mock_visible_workflow_needs_no_evaluator_files(data_root, tmp_path):
    shutil.copytree(data_root / "repair", tmp_path / "repair")
    shutil.copytree(data_root / "manifests", tmp_path / "manifests")
    record = run_visible_check(tmp_path, "clamp", candidate_origin="mock")
    assert not (tmp_path / "evaluation").exists()
    assert record["run_kind"] == "mock"
    assert record["execution"]["status"] == "not_executed"
    assert record["evaluation"] is None
    assert record["usage"]["cost_usd"] == 0


def test_job_contains_only_immutable_source_and_visible_tests(data_root):
    task = load_task(data_root / "repair", "clamp")
    candidate = MockProvider().propose(RepairRequest(task)).candidate
    job = VisibleJob.from_task(task, candidate)
    assert set(asdict(job)) == {"task_id", "source", "tests"}
    assert job.tests == task.repair_tests
    assert job.source == candidate.replacement_source


def test_job_rejects_cross_task_patch_before_execution(data_root):
    task = load_task(data_root / "repair", "clamp")
    with pytest.raises(ValidationError, match="task_id"):
        VisibleJob.from_task(task, Candidate("other", "solution.py", "def clamp(): return 1"))


def test_job_rejects_invalid_utf8(data_root):
    with pytest.raises(ValidationError, match="valid UTF-8"):
        replace(load_task(data_root / "repair", "clamp"), source="def clamp(): return '\ud800'")


@pytest.mark.docker
def test_live_visible_check_preserves_dataset(data_root, docker_executor):
    before = {path: path.read_bytes() for path in data_root.rglob("*.json")}
    task = load_task(data_root / "repair", "clamp")
    original = VisibleJob.from_task(task).execute(docker_executor)
    patched = VisibleJob.from_task(task, MockProvider().propose(RepairRequest(task)).candidate).execute(docker_executor)
    assert original.status == "failed", original
    assert patched.status == "passed", patched
    assert original.cleanup_confirmed is True and patched.cleanup_confirmed is True
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.docker
def test_candidate_can_edit_only_its_disposable_source_copy(data_root, docker_executor):
    task = load_task(data_root / "repair", "clamp")
    original = (data_root / "repair/clamp/task.json").read_bytes()
    tests = (
        "from pathlib import Path\nfrom solution import clamp\n"
        "def test_workspace_write():\n"
        "    Path('/workspace/solution.py').write_text('changed in this container only')\n"
        "    assert Path('/workspace/solution.py').read_text() == 'changed in this container only'\n"
    )
    result = docker_executor.run(task.source, tests)
    assert result.status == "passed", result
    assert result.cleanup_confirmed is True
    assert (data_root / "repair/clamp/task.json").read_bytes() == original
