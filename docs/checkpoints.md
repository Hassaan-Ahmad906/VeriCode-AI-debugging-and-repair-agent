# Fixed batches and resumption

Run from the repository root. The supplied configuration is fully offline:

```powershell
.\.venv\Scripts\python.exe -m vericode batch --run-dir artifacts/my-direct-batch
.\.venv\Scripts\python.exe -m vericode batch --run-dir artifacts/my-direct-batch --resume
```

The first command requires a new/empty directory. The second skips every durable
terminal outcome, including failed or rejected patches. `completed` means a
recorded outcome, not correctness. A finished batch reports `newly_completed: 0`
on resume; its total call count/cost remains unchanged. No model or Docker access
is needed when all tasks are already completed.

`--config` selects a complete versioned configuration (default:
`configs/offline_direct.json`). `--manifest` selects the fixed task list (default:
`data/manifests/development.json`); `--data-root` selects repair-visible data.
To run a Docker demonstration, copy the configuration to an ignored local file,
set `backend` to `docker`, and pass that file with a new run directory. The provider
remains mock; these are sandbox smoke checks, not live-model measurements.

Each batch stores:

- `batch.json`: configuration, ordered manifest, task fingerprints, Python/platform
  and source/harness fingerprints, batch ID, and the resolved Docker image ID.
- `events.jsonl`: a `started` event persisted before any model call, followed by
  a `completed` event containing the full repair record and checksum.
- `.lock`: present only while a controller owns the batch; prevents cooperating
  controllers from concurrently writing the same checkpoint.

Each terminal record includes its Git HEAD, runtime fingerprint, actual prompt,
candidate/diff, execution state, attempt history, and per-call usage. Git commits
may differ after a documentation commit; resume compares the actual source/runtime
fingerprint. Changes to code, Python/platform, task content/order, or configuration
require a new directory. Raw source bytes are fingerprinted; even line-ending
changes can invalidate resumption. Docker jobs use the recorded immutable image,
including on resume if its original tag moved. A missing old image blocks work.

Journal lines are bounded to 2 MiB, the journal to 64 MiB, and batches to 100 tasks.
Space for a maximum-sized terminal record is reserved before starting a task.
Writes flush and fsync. Checksums detect corruption, not authenticated provenance;
files and the host controller remain trusted. Filesystem failures or crashes can
still leave ambiguous state. No exactly-once guarantee is made for external calls.

Resumption refuses malformed/torn lines, checksum mismatches, duplicate starts,
overlapping tasks, and changed inputs. A start without a completed outcome is
uncertain: the controller may have sent a call or finished execution before its
record was saved. Automatic replay is blocked so unknown usage is not replaced
with a fresh successful run. Preserve the checkpoint for inspection; use a new
directory only for an explicitly new run. Do not label an incomplete checkpoint
as zero usage or a complete experiment.

Stale locks are not automatically removed. Confirm the previous controller has
stopped before manual lock recovery. Removing a lock does not resolve an uncertain
started task; the journal still blocks it. Unconfirmed Docker cleanup also blocks
further jobs. An infrastructure error is recorded and halts the current batch;
after resolving the infrastructure, resume can continue unstarted tasks while
retaining that failure. It never silently retries the completed failure.

Exit codes: 0 for completed mock/visible-pass batches, 1 for completed batches
containing rejected/failed outcomes, and 2 for infrastructure, pending work, or
checkpoint/configuration errors. Evaluation remains null in all Day 3 records.
