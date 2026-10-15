"""Check selected upstream fixtures/references only in the isolated runner."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from vericode.benchmark import QUIXBUGS_REVISION, verify_repair_freeze
from vericode.datasets import load_task
from vericode.docker_executor import DockerExecutor
from vericode.evaluation import load_evaluation_suite
from vericode.experiments import write_run
from vericode.generated_tests import expected_value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError(args.output)
    verify_repair_freeze(Path("data"))
    executor = DockerExecutor()
    executor.prepare()
    records = []
    for name in ("gcd", "find_first_in_sorted", "is_valid_parenthesization"):
        task = load_task(Path("data/repair"), "quix_" + name)
        suite = load_evaluation_suite(Path("data/evaluation"), task.task_id)
        upstream = Path("data/benchmark/quixbugs/upstream")
        pairs = [json.loads(line) for line in (upstream / f"json_testcases/{name}.json").read_text().splitlines() if line.strip()]
        if not all(type(expected_value(task.task_id, inputs)) is type(expected) and expected_value(task.task_id, inputs) == expected
                   for inputs, expected in pairs):
            raise ValueError("upstream expectations disagree with independent rules")
        tests = task.repair_tests + suite.tests.replace(f"from solution import {name}\n", "").replace("def test_case_", "def test_evaluation_case_")
        original = executor.run(task.source, tests)
        reference = executor.run((upstream / f"correct_python_programs/{name}.py").read_text(), tests)
        records.append({"task_id": task.task_id, "original": asdict(original), "reference": asdict(reference),
                        "upstream_cases": len(pairs), "expectations_agree_with_rules": True})
        if original.cleanup_confirmed is False or reference.cleanup_confirmed is False:
            break
    write_run(args.output, {"schema_version": 1, "run_kind": "benchmark_audit", "revision": QUIXBUGS_REVISION,
                            "image_id": executor.image_id, "records": records})
    print(json.dumps({"records": [{"task_id": r["task_id"], "original": r["original"]["status"],
                                  "reference": r["reference"]["status"]} for r in records]}))
    return 0 if len(records) == 3 and all(r["reference"]["status"] == "passed" and r["reference"]["cleanup_confirmed"] is True
                                         and r["original"]["status"] in ("failed", "timeout") and r["original"]["cleanup_confirmed"] is True for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
