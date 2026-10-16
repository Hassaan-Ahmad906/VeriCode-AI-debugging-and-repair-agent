# Attribution and artifact licensing

The reviewed QuixBugs files under `data/benchmark/quixbugs/upstream` come from
[jkoppel/QuixBugs](https://github.com/jkoppel/QuixBugs), revision
`4257f44b0ff1181dedaedee6a447e133219fcebf`. Its original MIT license and copyright
notice are preserved at `data/benchmark/quixbugs/upstream/LICENSE`. Adaptations,
case selection, hashes, limitations and inspected exclusions are documented in
`docs/benchmark.md` and the provenance files. No claim is made to authorship of
the upstream programs or reference solutions.

The self-authored development fixtures and teaching expression-repair examples
are separate from QuixBugs. See `src/vericode/training_data.py` for their source.

Optional pretrained Qwen2.5-Coder-1.5B-Instruct weights are published by Qwen under
[Apache-2.0](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct). They are not
committed or redistributed here. A trained adapter remains derived from that
base; retain its base identity/license and the training/export manifests. The
merge recipe copies the base license into the exported model directory.

Optional Ollama portable binaries and llama.cpp conversion tools are downloaded
from their official repositories, with source/release identities recorded. They
are not committed here. Their licenses remain with those projects:
[Ollama](https://github.com/ollama/ollama/blob/main/LICENSE),
[llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE).
Installed Python dependencies retain their own distribution licenses.

This notice is not a new repository-wide license grant for original project
code. A project-wide license has not been selected by the owner.
