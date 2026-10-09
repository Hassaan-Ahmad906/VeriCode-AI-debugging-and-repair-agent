from dataclasses import asdict
import json

import pytest

from vericode.datasets import MAX_JSON_BYTES, TaskManifest, load_task, read_json
from vericode.evaluation import load_evaluation_suite
from vericode.schemas import RepairTask, ValidationError


def test_development_fixtures_have_separate_matching_suites(data_root):
    development = TaskManifest.load(data_root / "manifests/development.json")
    final = TaskManifest.load(data_root / "manifests/final.json")
    tasks = development.load_tasks(data_root / "repair")
    assert len(tasks) == 3
    assert not set(development.task_ids) & set(final.task_ids)
    assert final.task_ids == ()  # No claimed final evaluation data yet.
    for task in tasks:
        suite = load_evaluation_suite(data_root / "evaluation", task.task_id)
        assert suite.dataset_version == task.dataset_version
        assert "tests" not in asdict(task)
        assert suite.tests not in json.dumps(asdict(task))


@pytest.mark.parametrize("field,value,message", [
    ("schema_version", True, "schema_version"),
    ("schema_version", 2, "schema_version"),
    ("task_id", "../evaluation", "task_id"),
    ("specification", " ", "specification"),
    ("source", None, "source"),
    ("source", "x" * 32_769, "exceeds"),
    ("repair_tests", [], "repair_tests"),
    ("entry_point", "f(); attack()", "entry_point"),
    ("task_file", "../solution.py", "task_file"),
    ("task_file", "C:\\solution.py", "task_file"),
    ("split", "test", "split"),
], ids=["boolean-version", "unknown-version", "unsafe-id", "empty-spec", "null-source",
        "oversized-source", "wrong-tests-type", "invalid-entry", "relative-target",
        "absolute-target", "unknown-split"])
def test_malformed_task_has_field_error(data_root, field, value, message):
    data = asdict(load_task(data_root / "repair", "clamp"))
    data[field] = value
    with pytest.raises(ValidationError, match=message):
        RepairTask.from_dict(data)


def test_unknown_evaluator_fields_rejected(data_root):
    data = asdict(load_task(data_root / "repair", "clamp"))
    data["evaluation_tests"] = "do not expose"
    with pytest.raises(ValidationError, match="unknown fields"):
        RepairTask.from_dict(data)
    del data["evaluation_tests"]
    del data["specification"]
    with pytest.raises(ValidationError, match="missing fields.*specification"):
        RepairTask.from_dict(data)


@pytest.mark.parametrize("task_id", ["../clamp", "/tmp/clamp", "C:\\clamp", "clamp/other"])
def test_loader_rejects_unsafe_identifiers(data_root, task_id):
    with pytest.raises(ValidationError, match="task_id"):
        load_task(data_root / "repair", task_id)


@pytest.mark.parametrize("text,message", [
    ('{"x": 1, "x": 2}', "duplicate"),
    ('{bad json', "Expecting"),
    (' ' * (MAX_JSON_BYTES + 1), "exceeds"),
], ids=["duplicate-key", "invalid-json", "oversized-json"])
def test_bad_json_is_bounded_and_explained(tmp_path, text, message):
    path = tmp_path / "bad.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValidationError, match=message):
        read_json(path)


def test_manifest_rejects_duplicate_ids_and_split_mismatch(data_root, tmp_path):
    manifest = read_json(data_root / "manifests/development.json")
    path = tmp_path / "manifest.json"
    manifest["task_ids"] = ["clamp", "clamp"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValidationError, match="duplicate"):
        TaskManifest.load(path)
    manifest["task_ids"] = ["clamp"]
    manifest["split"] = "final"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValidationError, match="split/version"):
        TaskManifest.load(path).load_tasks(data_root / "repair")


def test_task_id_must_match_requested_directory(data_root, tmp_path):
    data = asdict(load_task(data_root / "repair", "clamp"))
    directory = tmp_path / "different"
    directory.mkdir()
    (directory / "task.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError, match="requested.*loaded"):
        load_task(tmp_path, "different")
