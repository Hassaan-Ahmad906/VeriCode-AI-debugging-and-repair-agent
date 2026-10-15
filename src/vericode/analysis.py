"""Traceable offline demonstration tables, case analysis, and optional plots."""

from collections import defaultdict
import csv
import hashlib
import json
import os
import importlib.util
import importlib.metadata
from pathlib import Path
from tempfile import TemporaryDirectory

from vericode.batch import runtime_fingerprint
from vericode.checkpoints import decode_json, fingerprint, locked_directory
from vericode.experiments import _git_revision, write_run
from vericode.metrics import evaluation_metrics
from vericode.model_io import CallRecord, Usage, summarize_calls
from vericode.protocol import STRATEGIES
from vericode.records import read_record
from vericode.study import load_study
from vericode.schemas import ValidationError

ANALYSIS_VERSION = "demonstration-analysis-v1"


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_name(path):
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def study_rows(directory: Path):
    with locked_directory(directory, resume=True):
        protocol, records = load_study(directory)
        manifest_path = directory / "files.sha256.json"
        if manifest_path.exists():
            manifest = read_record(manifest_path)
            for name in ("batch.json", "events.jsonl", "protocol.json", "collection_summary.json"):
                if manifest.get(name) != _sha(directory / name):
                    raise ValidationError("archived evidence byte checksum mismatch")
        journal = directory / "events.jsonl"
        journal_sha = _sha(journal)
        line_numbers = {}
        with journal.open("rb") as stream:
            for line_number, line in enumerate(stream, 1):
                event = decode_json(line)
                if event["event"] == "completed":
                    line_numbers[event["task_id"]] = line_number
        rows = []
        for strategy in STRATEGIES:
            for task_id in protocol["manifest"]["task_ids"]:
                repair_key = f"repair__{strategy}__{task_id}"
                score_key = f"score__{strategy}__{task_id}"
                repair = records.get(repair_key, {}).get("payload")
                score = records.get(score_key, {}).get("payload")
                usage = repair["usage"] if repair else {}
                if repair:
                    ledger = tuple(CallRecord(**{key: call[key] for key in CallRecord.__dataclass_fields__ if key != "usage"},
                                              usage=Usage(**call["usage"])) for call in repair["model_calls"])
                    expected_usage = summarize_calls(ledger)
                    if any(usage.get(key) != value for key, value in expected_usage.items()):
                        raise ValidationError("repair usage summary disagrees with its call ledger")
                candidate_execution = score.get("candidate_execution") if score else None
                row = {"protocol_sha256": protocol["protocol_sha256"], "run_kind": protocol["run_kind"],
                       "split": protocol["split"], "strategy": strategy, "task_id": task_id,
                       "repair_status": repair["status"] if repair else "not_started",
                       "evaluation_status": score["status"] if score else "not_scored",
                       "candidate_execution_status": (candidate_execution["status"] if candidate_execution else
                                                      "not_submitted" if score and score["status"] == "no_candidate" else
                                                      "blocked" if score else "not_scored"),
                       "candidate_changed": repair.get("candidate_changed") if repair else None,
                       "agent_accepted": repair.get("agent_accepted") if repair else None,
                       "suite_passed": score.get("suite_passed") if score else None,
                       "baseline_suite_passed": score.get("baseline_suite_passed") if score else None,
                       "regression": score.get("regression") if score else None,
                       "accepted_but_failed": score.get("accepted_but_failed") if score else None,
                       "mock_calls": usage.get("model_calls"), "repair_attempts": usage.get("attempts"),
                       "repair_responses": usage.get("repair_responses"),
                       "test_generation_calls": repair.get("test_generation", {}).get("usage", {}).get("model_calls", 0) if repair else None,
                       "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                       "api_cost_usd": usage.get("cost_usd"), "known_api_cost_usd": usage.get("known_cost_usd", 0),
                       "known_input_tokens": usage.get("known_input_tokens", 0), "known_output_tokens": usage.get("known_output_tokens", 0),
                       "repair_wall_seconds": repair.get("controller_duration_seconds") if repair else None,
                       "evaluation_wall_seconds": score.get("controller_duration_seconds") if score else None,
                       "repair_record_sha256": fingerprint(repair) if repair else None,
                       "score_record_sha256": fingerprint(score) if score else None,
                       "repair_event_line": line_numbers.get(repair_key), "score_event_line": line_numbers.get(score_key),
                       "source_directory": _source_name(directory), "journal_sha256": journal_sha,
                       "live_model_calls": 0}
                rows.append(row)
        source = {"directory": _source_name(directory), "protocol_sha256": protocol["protocol_sha256"],
                  "git_commit": protocol["git_commit"], "runtime": protocol["runtime"], "journal_sha256": journal_sha,
                  "complete": len(records) == 2 * len(rows), "run_kind": protocol["run_kind"], "split": protocol["split"]}
    return rows, source


def summarize_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["protocol_sha256"], row["run_kind"], row["split"], row["strategy"])].append(row)
    summaries = []
    for (protocol_sha, kind, split, strategy), group in groups.items():
        scores = [{"suite_passed": row["suite_passed"], "baseline_suite_passed": row["baseline_suite_passed"],
                   "agent_accepted": row["agent_accepted"], "regression": row["regression"],
                   "accepted_but_failed": row["accepted_but_failed"], "status": row["evaluation_status"],
                   "candidate_execution": {"status": row["candidate_execution_status"]}} for row in group]
        summary = {"protocol_sha256": protocol_sha, "run_kind": kind, "split": split, "strategy": strategy,
                   **evaluation_metrics(scores), "live_model_calls": 0,
                   "not_scored": sum(row["evaluation_status"] == "not_scored" for row in group),
                   "unsubmitted_candidates": sum(row["evaluation_status"] == "no_candidate" for row in group),
                   "repair_statuses": {status: sum(row["repair_status"] == status for row in group)
                                       for status in sorted({row["repair_status"] for row in group})}}
        for key in ("mock_calls", "repair_attempts", "repair_responses", "test_generation_calls", "input_tokens", "output_tokens", "api_cost_usd",
                    "repair_wall_seconds", "evaluation_wall_seconds"):
            values = [row[key] for row in group]
            summary[key] = sum(values) if all(value is not None for value in values) else None
        for key in ("known_api_cost_usd", "known_input_tokens", "known_output_tokens"):
            summary[key] = sum(row[key] for row in group)
        summaries.append(summary)
    return summaries


def _csv(path, rows):
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "unknown" if value is None else json.dumps(value, sort_keys=True) if isinstance(value, dict) else value
                             for key, value in row.items()})


def _figure(output, summaries):
    # Isolate Matplotlib's optional font/config cache; never start a GUI.
    with TemporaryDirectory(prefix="vericode-plot-") as cache:
        previous = os.environ.get("MPLCONFIGDIR")
        os.environ["MPLCONFIGDIR"] = cache
        try:
            try:
                import matplotlib
                matplotlib.use("Agg", force=True)
                import matplotlib.pyplot as plt
            except ImportError:
                raise ValidationError("plotting requires the optional analysis extra: pip install -e '.[analysis]'") from None
            labels = [f"{row['split'].title()} {dict(direct='A', feedback='B', augmented='C')[row['strategy']]}" for row in summaries]
            with plt.rc_context({"svg.hashsalt": "vericode-day6-v1", "svg.fonttype": "none", "font.size": 10}):
                fig, axes = plt.subplots(1, 2, figsize=(12, max(5.5, len(labels) * 0.65 + 1.6)))
                fig.subplots_adjust(top=0.77, bottom=0.15, left=0.13, right=0.98, wspace=0.48)
                fig.suptitle("Pipeline demonstrations (no LLM measurements)", fontsize=14, y=0.98)
                passed = [row["evaluation_passed"] for row in summaries]
                failed = [row["evaluation_failed"] for row in summaries]
                unresolved = [row["evaluation_unknown"] for row in summaries]
                positions = list(range(len(labels)))
                axes[0].barh(positions, passed, color="#27856c", label="Known suite pass")
                axes[0].barh(positions, failed, left=passed, color="#c45d48", label="Known suite failure")
                axes[0].barh(positions, unresolved, left=[p + f for p, f in zip(passed, failed)], color="#a5abb4", label="Unresolved / unsubmitted")
                axes[0].set_yticks(positions, labels)
                axes[0].set(title="Independent suite observations", xlabel="Tasks retained in denominator")
                handles, legend_labels = axes[0].get_legend_handles_labels()
                fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 0.91), ncol=3, frameon=False, fontsize=9)
                for position, counts in zip(positions, zip(passed, failed, unresolved)):
                    offset = 0
                    for index, count in enumerate(counts):
                        if count:
                            axes[0].text(offset + count / 2, position, str(count), ha="center", va="center",
                                         color="white" if index < 2 else "black", fontweight="bold")
                        offset += count
                axes[0].set_xticks(range(max(row["tasks"] for row in summaries) + 1))
                axes[0].set_xlim(0, max(row["tasks"] for row in summaries) + 0.2)
                axes[0].invert_yaxis()
                bars = axes[1].barh(positions, [row["mock_calls"] or 0 for row in summaries], color="#426a9d")
                axes[1].set_yticks(positions, labels)
                for bar, row in zip(bars, summaries):
                    axes[1].text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                                 "unknown" if row["mock_calls"] is None else str(row["mock_calls"]), va="center")
                axes[1].set(title="Actual mock transport invocations", xlabel="Test generation + repair calls; no paid calls")
                axes[1].set_xlim(0, max([row["mock_calls"] or 0 for row in summaries]) + 2)
                axes[1].invert_yaxis()
                fig.text(0.5, 0.02, "Scripted development answers and unchanged final mocks; no paid API calls. Methods are not compute matched.", ha="center", fontsize=8)
                fig.savefig(output, format="svg", metadata={"Date": None, "Creator": f"VeriCode / Matplotlib {matplotlib.__version__}"})
                # Matplotlib path lines have trailing spaces; normalize equivalent
                # XML whitespace before recording artifact byte checksums.
                output.write_text("\n".join(line.rstrip() for line in output.read_text(encoding="utf-8").splitlines()) + "\n",
                                  encoding="utf-8", newline="\n")
                fig.savefig(output.with_suffix(".png"), dpi=160, metadata={"Software": f"VeriCode / Matplotlib {matplotlib.__version__}"})
                plt.close(fig)
            return matplotlib.__version__
        finally:
            if previous is None:
                os.environ.pop("MPLCONFIGDIR", None)
            else:
                os.environ["MPLCONFIGDIR"] = previous


def generate_report(directories, output: Path, *, plots=False):
    if output.exists() or output.is_symlink():
        raise ValidationError("analysis output must be a new directory")
    if not directories:
        raise ValidationError("analysis requires at least one study directory")
    if plots and importlib.util.find_spec("matplotlib") is None:
        raise ValidationError("plotting requires the optional analysis extra: pip install -e '.[analysis]'")
    rows, sources = [], []
    for directory in directories:
        study_data, source = study_rows(directory)
        if any(existing["protocol_sha256"] == source["protocol_sha256"] for existing in sources):
            raise ValidationError("duplicate study protocol; refusing to double-count outcomes")
        rows.extend(study_data)
        sources.append(source)
    summaries = summarize_rows(rows)
    cases = [{key: row[key] for key in ("protocol_sha256", "split", "strategy", "task_id", "repair_status", "candidate_execution_status", "accepted_but_failed",
                                       "repair_record_sha256", "score_record_sha256", "source_directory", "repair_event_line", "score_event_line")}
             for row in rows if row["accepted_but_failed"] is True
             or row["candidate_execution_status"] in ("timeout", "test_error", "infrastructure_error", "output_limit", "resource_limit")
             or row["repair_status"] not in ("visible_passed", "candidate_ready")]
    output.mkdir(parents=True)
    _csv(output / "tasks.csv", rows)
    _csv(output / "summary.csv", summaries)
    plot_version = _figure(output / "outcomes-and-calls.svg", summaries) if plots else None
    result = {"schema_version": 1, "analysis_version": ANALYSIS_VERSION, "measured_llm_results_available": False,
              "live_model_calls": 0, "compute_matched": False, "sources": sources, "summaries": summaries,
              "failure_cases": cases, "analysis_git_head": _git_revision(), "analysis_runtime": runtime_fingerprint(),
              "analysis_source_sha256": _sha(Path(__file__)), "matplotlib_version": plot_version,
              "plotting_environment": {name: importlib.metadata.version(name) for name in (
                  "matplotlib", "contourpy", "cycler", "fonttools", "kiwisolver", "numpy", "packaging", "pillow",
                  "pyparsing", "python-dateutil", "six")} if plots else None,
              "limitations": ["Mock and sandbox demonstrations only; no measured LLM effect or hosted-token comparison.",
                              "Small public inspected task subsets; no significance or generalisation claim.",
                              "Unknown outcomes and missing work remain in denominators; bounds are not confidence intervals.",
                              "Regressions are suite-level; baseline-pass/known-candidate denominators are explicit.",
                              "Git HEAD may precede uncommitted analysis code; actual source/runtime fingerprints are recorded."]}
    write_run(output / "analysis.json", result)
    lines = ["# Pipeline demonstration analysis\n", "**No measured LLM results are available.** Providers are scripted development fixtures or unchanged final-task mocks. These observations validate collection/evaluation/reporting only.\n",
             "| Split | Method | Tasks | Pass | Fail | Unknown | Mock calls | API USD | Input tokens | Output tokens |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    show = lambda value: "unknown" if value is None else str(value)
    for row in summaries:
        lines.append("| " + " | ".join(show(row[key]) for key in ("split", "strategy", "tasks", "evaluation_passed", "evaluation_failed", "evaluation_unknown", "mock_calls", "api_cost_usd", "input_tokens", "output_tokens")) + " |")
    lines += ["\nInput/output tokens remain unknown when not supplied; zero-call runs consumed none. API dollars exclude local compute. All methods retain their actual calls; they are not compute-matched.\n",
              "Each tasks.csv row records exact repair/score payload hashes, journal hash and completed-event line numbers. summary.csv and analysis.json preserve source protocol identities, incomplete work, execution-status distributions, latency, known subtotals, explicit metric denominators and all selected failure cases. Protocols and byte-checked JSONL evidence remain in the source directories.\n",
              "Failure cases below retain accepted-but-failing patches, candidate execution errors and terminal repair failures. Repeated-original stopping can leave a candidate unsubmitted. Missing-outcome bounds are not statistical confidence intervals. Suite regression rates require an observed original-suite pass and a known final-suite outcome; see the explicit denominators.\n",
              "Development and final splits remain separate, as does each protocol; no hosted pilot or measured result is pooled here. Source code, limits, image, prompts/oracles and available seeds are frozen in each protocol. Actual timing depends on this local Docker environment and is not a model-speed comparison.\n",
              "Reproduce tables with `vericode analyze --run-dir <evidence-directory> ... --output <new-directory>`. Add `--plot` with the optional analysis extra for a standalone Matplotlib SVG. Historical evidence can be analysed under later code; collection resume still rejects changed runtime.\n"]
    if cases:
        lines += ["## Failure cases\n", "| Split | Method | Task | Repair stop | Candidate evaluation | Repair / score event |",
                  "|---|---|---|---|---|---|"]
        locations = {source["protocol_sha256"]: Path(directory) for directory, source in zip(directories, sources)}
        for case in cases:
            try:
                relative = Path(os.path.relpath(locations[case["protocol_sha256"]] / "events.jsonl", output)).as_posix()
                links = " / ".join(f"[L{case[key]}]({relative}#L{case[key]})" if case[key] else "not recorded"
                                   for key in ("repair_event_line", "score_event_line"))
            except ValueError:
                links = "See exact hashes and event lines in tasks.csv"
            lines.append("| " + " | ".join(str(case[key]) for key in ("split", "strategy", "task_id", "repair_status", "candidate_execution_status")) + f" | {links} |")
    if plots:
        lines.append("![Observed suites and actual mock calls](outcomes-and-calls.png)\n\n[Standalone SVG](outcomes-and-calls.svg)\n")
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    hashes = {path.name: _sha(path) for path in sorted(output.iterdir()) if path.is_file()}
    write_run(output / "files.sha256.json", hashes)
    return {"schema_version": 1, "output": str(output), "study_count": len(sources), "task_rows": len(rows),
            "summary_rows": len(summaries), "measured_llm_results_available": False, "live_model_calls": 0}
