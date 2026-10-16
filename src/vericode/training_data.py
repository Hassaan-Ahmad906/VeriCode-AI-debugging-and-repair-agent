"""Self-authored toy repair examples; no repository fixtures or evaluator reads.

Family-level splits keep renamed variants of an operation in the same split.
This small teaching dataset is not sufficient evidence of useful general repair.
"""

from dataclasses import asdict
import ast
import json

from vericode.checkpoints import fingerprint
from vericode.model_io import RepairRequest
from vericode.patches import validate_candidate
from vericode.schemas import Candidate, RepairTask

# family, arguments, specification, buggy expression, corrected expression, case
FAMILIES = (
    ("addition", "a, b", "Return the sum of a and b.", "a - b", "a + b", "(2, 3) == 5"),
    ("difference", "a, b", "Subtract b from a.", "a + b", "a - b", "(7, 2) == 5"),
    ("product", "a, b", "Return the product of a and b.", "a + b", "a * b", "(3, 4) == 12"),
    ("absolute", "a", "Return the absolute value of a.", "a", "abs(a)", "(-3) == 3"),
    ("square", "a", "Return a squared.", "a * 2", "a * a", "(3) == 9"),
    ("even", "a", "Return True exactly when integer a is even.", "a % 2 == 1", "a % 2 == 0", "(4) is True"),
    ("negative", "a", "Return True exactly when a is strictly negative.", "a <= 0", "a < 0", "(0) is False"),
    ("increment", "a", "Return a plus one.", "a - 1", "a + 1", "(3) == 4"),
    ("maximum", "a, b", "Return the larger of a and b.", "min(a, b)", "max(a, b)", "(2, 7) == 7"),
    ("length", "a", "Return the number of items in list a.", "len(a) + 1", "len(a)", "([1, 2]) == 2"),
    ("minimum", "a, b", "Return the smaller of a and b.", "max(a, b)", "min(a, b)", "(2, 7) == 2"),
    ("decrement", "a", "Return a minus one.", "a + 1", "a - 1", "(3) == 2"),
)
VALIDATION_FAMILIES = frozenset({"minimum", "decrement"})


def build_examples(variants=12):
    if type(variants) is not int or not 1 <= variants <= 100:
        raise ValueError("variants must be between 1 and 100")
    rows = {"train": [], "validation": []}
    for family, arguments, spec, buggy, correct, case in FAMILIES:
        split = "validation" if family in VALIDATION_FAMILIES else "train"
        for variant in range(variants):
            name = f"repair_{family}_{variant}"
            source = f"def {name}({arguments}):\n    return {buggy}\n"
            target = f"def {name}({arguments}):\n    return {correct}\n"
            tests = f"from solution import {name}\n\ndef test_example():\n    assert {name}{case}\n"
            task = RepairTask(1, "authored-training-v1", name, "development", spec,
                              name, "solution.py", source, tests)
            candidate = Candidate(name, "solution.py", target)
            validate_candidate(task, candidate)
            ast.parse(tests)  # syntax only; training never runs candidate/test code
            messages = [{"role": "user", "content": RepairRequest(task).prompt()},
                        {"role": "assistant", "content": json.dumps(asdict(candidate), sort_keys=True)}]
            rows[split].append({"family": family, "task_id": name, "messages": messages})
    return rows


def dataset_manifest(rows):
    return {"schema_version": 1, "dataset_version": "authored-training-v1",
            "provenance": "Self-authored expression repairs, created for VeriCode; no benchmark/reference/evaluator input.",
            "split_unit": "operation family; renamed variants stay together",
            "limitations": "Small repetitive teaching set; validation loss is not execution correctness or general repair ability.",
            "splits": {split: {"examples": len(items), "families": sorted({row['family'] for row in items}),
                               "sha256": fingerprint(items)} for split, items in rows.items()}}
