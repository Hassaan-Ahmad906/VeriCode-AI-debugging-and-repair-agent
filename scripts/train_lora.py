"""Free-GPU LoRA training recipe. Run in the provided Colab notebook, not CPU.

Training consumes data as text. It never executes a generated function or test.
No paid API, hub upload, experiment tracker, or remote-code trust is enabled.
"""

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess

from vericode.training_data import build_examples, dataset_manifest


def encode_example(tokenizer, messages, max_length):
    prefix = tokenizer.apply_chat_template(messages[:1], tokenize=True, add_generation_prompt=True)
    full = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False)
    if full[:len(prefix)] != prefix or len(full) <= len(prefix):
        raise ValueError("Chat template does not preserve the assistant prefix")
    if len(full) > max_length:
        raise ValueError("Example exceeds context limit; refusing silent truncation")
    return {"input_ids": full, "attention_mask": [1] * len(full),
            "labels": [-100] * len(prefix) + full[len(prefix):]}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    parser.add_argument("--revision", required=True, help="immutable Hugging Face model commit")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--smoke", action="store_true", help="two optimizer steps to verify runtime before full training")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output must be new; preserve earlier adapters")
    if len(args.revision) != 40 or any(c not in "0123456789abcdef" for c in args.revision):
        parser.error("revision must be an immutable 40-character model commit")
    import torch
    if not torch.cuda.is_available():
        parser.error("No CUDA GPU. Select a free Colab GPU runtime; CPU training is intentionally blocked.")
    from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                              EarlyStoppingCallback, Trainer, TrainingArguments, set_seed)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    set_seed(42)
    args.output.mkdir(parents=True)
    rows = build_examples()
    manifest = dataset_manifest(rows)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, revision=args.revision, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    encoded = {split: [encode_example(tokenizer, row["messages"], 1024) for row in examples]
               for split, examples in rows.items()}
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                      bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype)
    model = AutoModelForCausalLM.from_pretrained(args.base_model, revision=args.revision,
              trust_remote_code=False, use_safetensors=True, quantization_config=quantization,
              device_map={"": 0}, torch_dtype=dtype)
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                          target_modules=["q_proj", "v_proj"], bias="none", task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    def collate(batch):
        width = max(len(item["input_ids"]) for item in batch)
        result = {}
        for field, padding in (("input_ids", tokenizer.pad_token_id), ("attention_mask", 0), ("labels", -100)):
            result[field] = torch.tensor([item[field] + [padding] * (width - len(item[field])) for item in batch])
        return result

    training = TrainingArguments(output_dir=str(args.output / "checkpoints"),
        num_train_epochs=args.epochs, max_steps=2 if args.smoke else -1,
        per_device_train_batch_size=1, per_device_eval_batch_size=1,
        gradient_accumulation_steps=8, learning_rate=1e-4, warmup_ratio=0.05,
        bf16=dtype == torch.bfloat16, fp16=dtype == torch.float16,
        gradient_checkpointing=True, optim="adamw_torch", logging_steps=1,
        eval_strategy="epoch", save_strategy="epoch", save_total_limit=1,
        load_best_model_at_end=True, metric_for_best_model="eval_loss",
        greater_is_better=False, report_to="none", seed=42, data_seed=42,
        push_to_hub=False, dataloader_num_workers=0)
    trainer = Trainer(model=model, args=training, train_dataset=encoded["train"],
                      eval_dataset=encoded["validation"], data_collator=collate,
                      callbacks=[EarlyStoppingCallback(early_stopping_patience=1)])
    before = trainer.evaluate()
    result = trainer.train()
    after = trainer.evaluate()
    adapter = args.output / "adapter"
    trainer.save_model(str(adapter))
    tokenizer.save_pretrained(str(adapter))
    manifest.update({"base_model": args.base_model, "base_revision": args.revision,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "gpu": torch.cuda.get_device_name(0), "smoke_only": args.smoke,
        "epochs_requested": args.epochs, "seed": 42,
        "packages": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "bitsandbytes", "accelerate")},
        "validation_before": before, "training": result.metrics, "validation_after": after,
        "claims": "Loss only. No independent execution evaluation, no demonstrated generalisation, no measured repair improvement."})
    (args.output / "training_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Saved adapter and provenance to {args.output}; do not infer repair correctness from loss.")


if __name__ == "__main__":
    main()
