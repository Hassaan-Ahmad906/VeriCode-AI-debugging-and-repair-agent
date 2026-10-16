# Free customization on a laptop without a GPU

This laptop has an i7-1355U, about 16 GB RAM and Intel Iris Xe graphics. Use the
laptop for local quantized inference, the application and Docker evaluation.
Use a free Colab GPU, when available, for parameter-efficient fine-tuning.
Do not attempt to pretrain a competitive coding language model on this hardware.

[Open the training notebook in Google Colab](https://colab.research.google.com/github/Hassaan-Ahmad906/VeriCode-AI-debugging-and-repair-agent/blob/master/notebooks/train_free_colab.ipynb).

Sign in to your own Google account, select Runtime > Change runtime type > GPU,
and run the cells in order. No payment, API key, Drive access or model upload is
needed. If the free tier offers no GPU, stop and retry later. The assistant cannot
sign in, allocate a GPU under your account or run this notebook from the local
workspace. No GPU training result or trained adapter is claimed in this release.

If the checkout cell previously raised `FileExistsError` for `/content/VeriCode`,
replace that cell with the current notebook's setup cell and run it again. It
verifies the checkout root and GitHub origin, then reuses the existing revision
without pulling, deleting files or discarding training outputs. Continue from
the next cell; do not reset a working GPU runtime to fix a checkout rerun.

The notebook:

1. Requires CUDA before training; pins Transformers, PEFT, bitsandbytes and
   Accelerate while retaining Colab's installed PyTorch/CUDA combination.
2. Clones the public repository and records the actual code commit. Resolves the
   public Qwen2.5-Coder-1.5B-Instruct checkpoint to an immutable model revision.
3. Builds 120 training and 24 validation examples from self-authored expression
   repairs. Operation families, including all renamed variants, stay in one split.
   No QuixBugs, benchmark references or frozen evaluator files enter this dataset.
4. Runs a two-optimizer-step smoke check, then a separate run with at most three
   epochs, batch size 1, accumulation 8, rank 8 q/v LoRA adapters and 4-bit NF4.
   Early stopping retains the best validation loss. Prompt tokens are masked;
   examples longer than the context allowance are rejected, never truncated.
5. Saves safetensors adapters/tokenizer and a manifest containing data hashes,
   code/model identities, GPU, package versions and observed losses. Downloads
   the adapter archive to your laptop before the free session expires.

These are **custom adapter weights on an existing pretrained model**, not a new
foundation model. The teaching data is small and repetitive. Renamed variants are
not independent samples. Validation loss does not measure execution correctness,
and extra epochs may overfit. Expand training only with reviewed, licensed repair
pairs, deduplicate by problem/normalized structure, preserve task-level splits,
and compare base and adapted models with the same independent execution protocol.

To use a trained adapter locally, keep the exact base revision. The notebook's
optional export cells use `scripts/merge_adapter.py`, a pinned llama.cpp revision,
CPU quantization to Q4_K_M, a GGUF checksum and the preserved base license. These
cloud export cells have not been runtime-verified on this GPU-less laptop.
Qwen safetensors
adapters are not universally supported by Ollama's direct ADAPTER import. Merge
the adapter into the same base with PEFT on the cloud runtime, export the merged
model to GGUF using a recorded llama.cpp conversion revision, and quantize for CPU
inference. Import with an Ollama Modelfile using `FROM ./your-model.gguf`, then
`ollama create vericode-custom -f Modelfile`. Select `vericode-custom` in the UI.
Retain the adapter, original base license, conversion revision and model hashes.
Conversion and repair-quality validation are separate steps; the downloaded
adapter alone is not yet a laptop-ready GGUF model.

Sources: [Qwen model card and Apache-2.0 license](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct),
[PEFT quantization](https://huggingface.co/docs/peft/developer_guides/quantization),
[PEFT quicktour](https://huggingface.co/docs/peft/quicktour),
[Colab limits](https://research.google.com/colaboratory/faq.html),
[Ollama model imports](https://docs.ollama.com/import).
