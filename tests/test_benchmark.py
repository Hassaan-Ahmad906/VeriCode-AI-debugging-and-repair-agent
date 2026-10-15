from dataclasses import asdict
import hashlib
import json
import shutil

import pytest

from vericode.benchmark import QUIXBUGS_VERSION, verify_repair_freeze
from vericode.datasets import TaskManifest, load_task
from vericode.generated_tests import expected_value
from vericode.model_io import RepairRequest
from vericode.providers import MockProvider
from vericode.schemas import ValidationError


def test_frozen_splits_and_noop_final_mock_need_no_evaluator(data_root, tmp_path):
    shutil.copytree(data_root / "repair", tmp_path / "repair")
    shutil.copytree(data_root / "manifests", tmp_path / "manifests")
    freeze = verify_repair_freeze(tmp_path)
    assert not set(freeze["splits"]["development"]["tasks"]) & set(freeze["splits"]["final"]["tasks"])
    manifest = TaskManifest.load(tmp_path / "manifests/final.json")
    for task in manifest.load_tasks(tmp_path / "repair"):
        assert task.dataset_version == QUIXBUGS_VERSION and task.split == "final"
        response = MockProvider().propose(RepairRequest(task))
        assert response.candidate.replacement_source == task.source
        assert len(response.calls) == 1 and "reference" not in asdict(RepairRequest(task))


def test_changed_task_breaks_freeze(data_root, tmp_path):
    shutil.copytree(data_root / "repair", tmp_path / "repair")
    shutil.copytree(data_root / "manifests", tmp_path / "manifests")
    path = tmp_path / "repair/quix_gcd/task.json"
    task = json.loads(path.read_text())
    task["source"] += "\n# changed\n"
    path.write_text(json.dumps(task))
    with pytest.raises(ValidationError, match="freeze mismatch"):
        verify_repair_freeze(tmp_path)


def test_vendored_bytes_and_all_upstream_expectations(data_root):
    root = data_root / "benchmark/quixbugs"
    provenance = json.loads((root / "provenance.json").read_text())
    for name, digest in provenance["upstream_sha256"].items():
        path = root / "upstream" / name
        if path.exists():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    for name in provenance["included_programs"]:
        task = load_task(data_root / "repair", "quix_" + name)
        assert task.source == (root / f"upstream/python_programs/{name}.py").read_text()
        pairs = [json.loads(line) for line in (root / f"upstream/json_testcases/{name}.json").read_text().splitlines()]
        for args, expected in pairs:
            actual = expected_value(task.task_id, args)
            assert type(actual) is type(expected) and actual == expected
