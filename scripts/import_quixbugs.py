"""Offline, pinned three-function adapter. Never import upstream Python modules."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from vericode.checkpoints import fingerprint
from vericode.datasets import TaskManifest

REVISION = "4257f44b0ff1181dedaedee6a447e133219fcebf"
VERSION = "quixbugs-4257f44-v1"
NAMES = ("gcd", "find_first_in_sorted", "is_valid_parenthesization")
SPECS = {
    "gcd": "Given nonnegative integers a and b, return their greatest common divisor. Define gcd(0, 0) as 0.",
    "find_first_in_sorted": "Given a sorted list arr of integers and integer x, return the first index of x, or -1 if absent. Empty lists are allowed.",
    "is_valid_parenthesization": "Given a string containing only '(' and ')', return whether its parentheses are balanced: every prefix has nonnegative balance and the total balance is zero. Empty input is balanced.",
}
VISIBLE = {"gcd": ([17, 0], 17), "find_first_in_sorted": ([[3, 4, 5, 5, 5, 5, 6], 5], 2),
           "is_valid_parenthesization": (["((()()))()"], True)}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")


def render(name, cases):
    lines = [f"from solution import {name}\n"]
    for i, (args, expected) in enumerate(cases):
        lines.append(f"\ndef test_case_{i}():\n    assert {name}(*{args!r}) == {expected!r}\n")
    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="pinned upstream checkout or reviewed source cache")
    args = parser.parse_args()
    # Pin all reviewed bytes, not merely the supplied revision label.
    expected = json.loads(Path("data/benchmark/quixbugs/provenance.json").read_text(encoding="utf-8"))["upstream_sha256"]
    for path, digest in expected.items():
        if hashlib.sha256((args.source / path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"upstream hash mismatch: {path}")
    for path in expected:
        if path in ("legal_notes.txt", "README.md", "conftest.py", "tester.py"):
            continue  # reviewed metadata, no need to redistribute public email correspondence
        destination = Path("data/benchmark/quixbugs/upstream") / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.source / path, destination)
    for name in NAMES:
        task_id = "quix_" + name
        pairs = [json.loads(line) for line in (args.source / f"json_testcases/{name}.json").read_text().splitlines() if line.strip()]
        # Keep one upstream visible case; all remaining upstream cases evaluator-only.
        hidden = [pair for pair in pairs if pair != list(VISIBLE[name])]
        if name == "find_first_in_sorted":
            hidden.append([[[], 1], -1])  # documented adapter edge case, absent upstream
        task = {"schema_version": 1, "dataset_version": VERSION, "task_id": task_id, "split": "final",
                "specification": SPECS[name], "entry_point": name, "task_file": "solution.py",
                "source": (args.source / f"python_programs/{name}.py").read_text(encoding="utf-8"),
                "repair_tests": render(name, [VISIBLE[name]])}
        write_json(Path("data/repair") / task_id / "task.json", task)
        write_json(Path("data/evaluation") / task_id / "suite.json",
                   {"schema_version": 1, "dataset_version": VERSION, "task_id": task_id, "tests": render(name, hidden)})
    write_json(Path("data/manifests/final.json"), {"schema_version": 1, "dataset_version": VERSION,
               "split": "final", "task_ids": ["quix_" + name for name in NAMES]})
    repair_freeze = {}
    evaluation_freeze = {}
    for split in ("development", "final"):
        manifest = TaskManifest.load(Path(f"data/manifests/{split}.json"))
        tasks = manifest.load_tasks(Path("data/repair"))
        repair_freeze[split] = {"manifest": fingerprint(json.loads(Path(f"data/manifests/{split}.json").read_text())),
                                "tasks": {task.task_id: fingerprint(task.__dict__) for task in tasks}}
        evaluation_freeze[split] = {task.task_id: fingerprint(json.loads((Path("data/evaluation") / task.task_id / "suite.json").read_text())) for task in tasks}
    write_json(Path("data/manifests/repair_freeze.json"), {"schema_version": 1, "splits": repair_freeze})
    write_json(Path("data/benchmark/evaluation_freeze.json"), {"schema_version": 1, "splits": evaluation_freeze})
    print("Adapted three pinned final tasks; frozen disjoint repair/evaluation identities.")


if __name__ == "__main__":
    main()
