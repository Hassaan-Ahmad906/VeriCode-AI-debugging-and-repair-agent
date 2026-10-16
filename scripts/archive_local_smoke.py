"""Preserve every declared local smoke attempt, including failed trials."""

import hashlib
import json
from pathlib import Path

from vericode.checkpoints import fingerprint
from vericode.records import read_record


def main():
    root = Path(__file__).resolve().parents[1]
    names = ["day7-local-repair.json", "day7-local-structured-repair.json", "day7-local-direct-score.json",
             "day7-local-feedback.json", "day7-local-feedback-score.json",
             "day7-ui-local-repair.json", "day7-ui-local-score.json"]
    records = {name: read_record(root / "artifacts" / name) for name in names}
    repairs = {r["run_id"]: r for r in records.values() if "run_id" in r}
    for record in records.values():
        if "evaluation_id" in record:
            assert fingerprint(repairs[record["repair_run_id"]]) == record["repair_record_sha256"]
    output = root / "reports/day7/local-model"
    output.mkdir(parents=True, exist_ok=False)
    for name in names:
        (output / name).write_bytes((root / "artifacts" / name).read_bytes())
    model_path = root / "artifacts/local-model/models/manifests/registry.ollama.ai/library/qwen2.5-coder/1.5b"
    model_bytes = model_path.read_bytes()
    (output / "ollama-model-manifest.json").write_bytes(model_bytes)
    summary = {"schema_version": 1, "kind": "development engineering smoke checks, not a controlled experiment",
        "model_tag": "qwen2.5-coder:1.5b", "ollama_version": "0.40.5",
        "model_manifest_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "current_local_adapter_sha256": hashlib.sha256((root / "src/vericode/local_provider.py").read_bytes()).hexdigest(),
        "provenance_limit": "Records identify HEAD with local edits; initial JSON-only adapter differed from subsequent structured-schema adapter. No frozen code/model experiment or A/B effect is claimed.",
        "trials": [{"file": name, "status": record["status"], "usage": record["usage"]}
                   for name, record in records.items() if "run_id" in record],
        "total_model_calls": sum(r["usage"]["model_calls"] for r in repairs.values()),
        "input_tokens": sum(r["usage"]["input_tokens"] for r in repairs.values()),
        "output_tokens": sum(r["usage"]["output_tokens"] for r in repairs.values()), "api_cost_usd": 0.0,
        "cloud_training_completed": False}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
    (output / "files.sha256.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("total_model_calls", "input_tokens", "output_tokens", "api_cost_usd")}))


if __name__ == "__main__":
    main()
