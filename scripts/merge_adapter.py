"""Merge a completed teaching adapter with its exact base on the cloud runtime.

Produces a normal safetensors model for an explicit subsequent GGUF conversion.
Requires the GPU notebook dependencies; never executes model-generated code.
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.training_dir / "training_manifest.json").read_text(encoding="utf-8"))
    if manifest["smoke_only"] or args.output.exists():
        parser.error("require a complete training run and a new output directory")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from huggingface_hub import hf_hub_download
    model = AutoModelForCausalLM.from_pretrained(manifest["base_model"], revision=manifest["base_revision"],
            trust_remote_code=False, use_safetensors=True, torch_dtype=torch.float16,
            device_map="cpu", low_cpu_mem_usage=True)
    model = PeftModel.from_pretrained(model, str(args.training_dir / "adapter"))
    model = model.merge_and_unload(safe_merge=True)
    model.save_pretrained(args.output, safe_serialization=True, max_shard_size="2GB")
    tokenizer = AutoTokenizer.from_pretrained(manifest["base_model"], revision=manifest["base_revision"], trust_remote_code=False)
    tokenizer.save_pretrained(args.output)
    license_path = hf_hub_download(manifest["base_model"], "LICENSE", revision=manifest["base_revision"])
    (args.output / "LICENSE").write_bytes(Path(license_path).read_bytes())
    (args.output / "vericode_training_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Merged model saved to {args.output}; quantize and independently evaluate before use.")


if __name__ == "__main__":
    main()
