from copy import deepcopy
from dataclasses import replace
import json
import shutil

import pytest

from vericode import study
from vericode.checkpoints import fingerprint
from vericode.datasets import read_json
from vericode.protocol import freeze_protocol, study_config, validate_protocol
from vericode.run_config import AugmentedConfiguration, FeedbackConfiguration, RunConfiguration
from vericode.schemas import ValidationError


def configuration(backend="mock"):
    return {"schema_version": 1, "label": "test-pipeline", "paid_api_enabled": False,
            "spending_cap_usd": 0.0, "random_seed": None,
            "strategies": {config.strategy: config.to_dict() for config in (
                RunConfiguration(backend=backend), FeedbackConfiguration(backend=backend), AugmentedConfiguration(backend=backend))}}


def test_all_repairs_precede_scores_and_completed_resume_has_zero_calls(data_root, tmp_path, monkeypatch):
    protocol = freeze_protocol(data_root, configuration(), "development")
    events = []
    for name in ("record_direct_task", "record_feedback_task", "record_augmented_task", "score_record"):
        original = getattr(study, name)

        def wrap(*args, _original=original, _name=name, **kwargs):
            events.append("score" if _name == "score_record" else "repair")
            return _original(*args, **kwargs)

        monkeypatch.setattr(study, name, wrap)
    directory = tmp_path / "run"
    first = study.run_study(data_root, protocol, directory)
    assert events == ["repair"] * 9 + ["score"] * 9
    assert first["pending"] == 0 and first["usage"]["model_calls"] == 12
    assert first["evaluation"]["evaluation_unknown"] == 9
    before = (directory / "events.jsonl").read_bytes()
    monkeypatch.setattr(study, "make_executor", lambda *args: pytest.fail("completed resume must not start execution"))
    second = study.run_study(data_root, protocol, directory, resume=True)
    assert second["newly_completed"] == 0 and second["usage"] == first["usage"]
    assert (directory / "events.jsonl").read_bytes() == before
    loaded_protocol, records = study.load_study(directory)
    assert loaded_protocol["protocol_sha256"] == protocol["protocol_sha256"] and len(records) == 18


@pytest.mark.parametrize("field,value", [("paid_api_enabled", True), ("spending_cap_usd", 1), ("spending_cap_usd", False), ("random_seed", 7)])
def test_paid_or_unsupported_configuration_is_rejected(field, value):
    config = configuration()
    config[field] = value
    with pytest.raises(ValidationError):
        study_config(config)


def test_protocol_tampering_and_changed_runtime_are_rejected_before_calls(data_root, tmp_path, monkeypatch):
    protocol = freeze_protocol(data_root, configuration(), "final")
    corrupt = deepcopy(protocol)
    corrupt["configuration"]["label"] = "changed"
    with pytest.raises(ValidationError, match="checksum"):
        validate_protocol(corrupt)
    monkeypatch.setattr("vericode.protocol.runtime_fingerprint", lambda: {"changed": True})
    with pytest.raises(ValidationError, match="runtime changed"):
        study.run_study(data_root, protocol, tmp_path / "run")
    assert not (tmp_path / "run").exists()


def test_missing_final_candidate_is_retained_and_mock_never_claims_measurement(data_root, tmp_path):
    protocol = freeze_protocol(data_root, configuration(), "final")
    summary = study.run_study(data_root, protocol, tmp_path / "final")
    assert summary["run_kind"] == "mock" and summary["measured_llm_results_available"] is False
    assert summary["evaluation"]["tasks"] == 9 and summary["evaluation"]["evaluation_unknown"] == 9
    assert summary["evaluation"]["evaluation_pass_fraction"] is None


def test_uncertain_repair_start_is_never_replayed(data_root, tmp_path, monkeypatch):
    protocol = freeze_protocol(data_root, configuration(), "development")

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt("simulated uncertain call")

    monkeypatch.setattr(study, "record_direct_task", interrupted)
    directory = tmp_path / "uncertain"
    with pytest.raises(KeyboardInterrupt):
        study.run_study(data_root, protocol, directory)
    before = (directory / "events.jsonl").read_bytes()
    monkeypatch.setattr(study, "record_direct_task", lambda *args: pytest.fail("must not replay"))
    with pytest.raises(ValidationError, match="uncertain"):
        study.run_study(data_root, protocol, directory, resume=True)
    assert (directory / "events.jsonl").read_bytes() == before


def test_protocol_refuses_traversal_even_with_recomputed_checksum(data_root):
    protocol = freeze_protocol(data_root, configuration(), "development")
    protocol["split"] = "../../other"
    protocol["protocol_sha256"] = fingerprint({key: value for key, value in protocol.items() if key != "protocol_sha256"})
    with pytest.raises(ValidationError, match="invalid split"):
        validate_protocol(protocol)


def test_score_must_link_to_exact_saved_repair(data_root, tmp_path):
    protocol = freeze_protocol(data_root, configuration(), "development")
    directory = tmp_path / "links"
    study.run_study(data_root, protocol, directory)
    path = directory / "events.jsonl"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    score_event = next(event for event in events if event["event"] == "completed" and event["record"]["phase"] == "score")
    score_event["record"]["payload"]["repair_record_sha256"] = "0" * 64
    score_event["record_sha256"] = fingerprint(score_event["record"])
    path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
    with pytest.raises(ValidationError, match="exact repair"):
        study.load_study(directory)


@pytest.mark.docker
def test_docker_protocol_freezes_image_and_full_two_phase_study(data_root, tmp_path, monkeypatch):
    protocol = freeze_protocol(data_root, configuration("docker"), "development")
    assert protocol["docker_image_id"].startswith("sha256:")
    directory = tmp_path / "docker"
    first = study.run_study(data_root, protocol, directory)
    assert first["pending"] == 0, first
    assert first["usage"]["model_calls"] == 10
    assert first["evaluation"]["evaluation_passed"] == 7
    assert first["evaluation"]["evaluation_failed"] == first["evaluation"]["accepted_but_failed"] == 2
    monkeypatch.setattr(study, "DockerExecutor", lambda *args: pytest.fail("completed resume needs no Docker"))
    assert study.run_study(data_root, protocol, directory, resume=True)["newly_completed"] == 0
