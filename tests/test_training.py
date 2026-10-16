import ast
import importlib.util
import json
from pathlib import Path

from vericode.training_data import build_examples, dataset_manifest


def test_training_has_disjoint_families_deterministic_bytes_and_no_benchmark_inputs():
    rows = build_examples()
    train = {row["family"] for row in rows["train"]}
    validation = {row["family"] for row in rows["validation"]}
    assert not train & validation
    assert len(rows["train"]) == 120 and len(rows["validation"]) == 24
    assert dataset_manifest(rows) == dataset_manifest(build_examples())
    for examples in rows.values():
        for row in examples:
            prompt = row["messages"][0]["content"]
            assert "quix" not in prompt and "evaluation" not in prompt
            response = json.loads(row["messages"][1]["content"])
            ast.parse(response["replacement_source"])


def test_training_masks_prompt_and_refuses_truncation():
    script = Path(__file__).resolve().parents[1] / "scripts/train_lora.py"
    spec = importlib.util.spec_from_file_location("train_recipe", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            return [10, 11] if len(messages) == 1 else [10, 11, 12, 13]
    result = module.encode_example(Tokenizer(), [{}, {}], 8)
    assert result["labels"] == [-100, -100, 12, 13]
    import pytest
    with pytest.raises(ValueError, match="truncation"):
        module.encode_example(Tokenizer(), [{}, {}], 3)


def test_notebook_cells_compile_and_have_no_fabricated_outputs():
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "notebooks/train_free_colab.ipynb").read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == [] and cell["execution_count"] is None
            compile("".join(cell["source"]), "notebook-cell", "exec")


import pytest


@pytest.mark.docker
def test_authored_training_targets_pass_their_examples_in_docker(docker_executor):
    rows = build_examples(variants=1)
    source, tests = [], []
    for row in rows["train"] + rows["validation"]:
        task = json.loads(row["messages"][0]["content"].split("\n\n", 1)[1])
        candidate = json.loads(row["messages"][1]["content"])
        source.append(candidate["replacement_source"])
        tests.append(task["repair_tests"].replace("def test_example():", f"def test_{row['task_id']}():"))
    result = docker_executor.run("\n".join(source), "\n".join(tests))
    assert result.status == "passed" and result.tests_passed == 12
    assert result.cleanup_confirmed is True
