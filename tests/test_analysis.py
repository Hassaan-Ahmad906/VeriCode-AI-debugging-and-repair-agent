import csv
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from vericode.analysis import generate_report
from vericode.checkpoints import fingerprint
from vericode.records import read_record
from vericode.schemas import ValidationError

EVIDENCE = Path(__file__).resolve().parents[1] / "reports/day6/evidence"


def test_report_retains_unknowns_actual_calls_and_exact_event_links(tmp_path):
    output = tmp_path / "analysis"
    result = generate_report([EVIDENCE / "development", EVIDENCE / "final"], output)
    assert result["task_rows"] == 18 and result["summary_rows"] == 6
    analysis = read_record(output / "analysis.json")
    groups = {(row["split"], row["strategy"]): row for row in analysis["summaries"]}
    assert [groups[("development", method)]["mock_calls"] for method in ("direct", "feedback", "augmented")] == [3, 1, 6]
    assert [groups[("final", method)]["mock_calls"] for method in ("direct", "feedback", "augmented")] == [3, 0, 6]
    assert groups[("final", "direct")]["evaluation_unknown"] == 1
    assert groups[("final", "augmented")]["unsubmitted_candidates"] == 3
    assert groups[("final", "direct")]["evaluation_pass_fraction"] is None
    assert groups[("final", "feedback")]["input_tokens"] == 0
    assert groups[("final", "direct")]["input_tokens"] is None
    assert analysis["measured_llm_results_available"] is False and analysis["live_model_calls"] == 0
    rows = list(csv.DictReader((output / "tasks.csv").open(encoding="utf-8", newline="")))
    for row in rows:
        journal = EVIDENCE / row["split"] / "events.jsonl"
        lines = journal.read_bytes().splitlines()
        for phase in ("repair", "score"):
            event = json.loads(lines[int(row[f"{phase}_event_line"]) - 1])
            assert fingerprint(event["record"]["payload"]) == row[f"{phase}_record_sha256"]
        assert hashlib.sha256(journal.read_bytes()).hexdigest() == row["journal_sha256"]
    assert sum(row["mock_calls"] for row in analysis["summaries"]) == 19


def test_duplicate_protocols_and_existing_outputs_are_rejected(tmp_path):
    output = tmp_path / "new"
    with pytest.raises(ValidationError, match="double-count"):
        generate_report([EVIDENCE / "development"] * 2, output)
    assert not output.exists()
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(ValidationError, match="new directory"):
        generate_report([EVIDENCE / "development"], output)
    assert sentinel.read_text() == "preserve"


def test_incomplete_but_certain_study_keeps_all_expected_task_rows(tmp_path):
    copied = tmp_path / "partial"
    copied.mkdir()
    shutil.copyfile(EVIDENCE / "development/batch.json", copied / "batch.json")
    events = (EVIDENCE / "development/events.jsonl").read_bytes().splitlines(keepends=True)
    # Stop after all nine durable repair outcomes, before any scoring start.
    (copied / "events.jsonl").write_bytes(b"".join(events[:18]))
    output = tmp_path / "report"
    generate_report([copied], output)
    result = read_record(output / "analysis.json")
    assert result["sources"][0]["complete"] is False
    assert all(group["tasks"] == group["evaluation_unknown"] == group["not_scored"] == 3 for group in result["summaries"])
    assert all(group["evaluation_pass_fraction"] is None for group in result["summaries"])


def test_archived_byte_corruption_is_not_analysed(tmp_path):
    copied = tmp_path / "corrupt"
    shutil.copytree(EVIDENCE / "development", copied)
    (copied / "collection_summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValidationError, match="byte checksum"):
        generate_report([copied], tmp_path / "report")


def test_optional_plot_exports_standalone_svg(tmp_path):
    pytest.importorskip("matplotlib")
    output = tmp_path / "plotted"
    generate_report([EVIDENCE / "development", EVIDENCE / "final"], output, plots=True)
    svg = (output / "outcomes-and-calls.svg").read_text(encoding="utf-8")
    assert "<svg" in svg and "no LLM measurements" in svg
    assert all(line == line.rstrip() for line in svg.splitlines())
    assert "Actual mock transport" in svg and "Unresolved / unsubmitted" in svg
    assert (output / "outcomes-and-calls.png").read_bytes().startswith(b"\x89PNG")
    hashes = read_record(output / "files.sha256.json")
    assert hashlib.sha256((output / "outcomes-and-calls.svg").read_bytes()).hexdigest() == hashes["outcomes-and-calls.svg"]


def test_inconsistent_usage_is_rejected_even_when_event_checksum_is_recomputed(tmp_path):
    copied = tmp_path / "bad-usage"
    copied.mkdir()
    shutil.copyfile(EVIDENCE / "development/batch.json", copied / "batch.json")
    events = [json.loads(line) for line in (EVIDENCE / "development/events.jsonl").read_bytes().splitlines()[:18]]
    completed = next(event for event in events if event["event"] == "completed")
    completed["record"]["payload"]["usage"]["input_tokens"] = 123
    completed["record_sha256"] = fingerprint(completed["record"])
    (copied / "events.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
    with pytest.raises(ValidationError, match="call ledger"):
        generate_report([copied], tmp_path / "report")
