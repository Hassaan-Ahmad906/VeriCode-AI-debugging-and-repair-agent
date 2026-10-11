# Local Docker execution

The mock demo remains the default. Candidate and test Python may run only through
`DockerExecutor`; there is no host execution fallback. Requires a local Linux
Docker daemon with cgroup v2, memory/swap, CPU quota, PID limits, and default
seccomp enabled. Earlier cgroup versions are rejected by preflight.

Build the trusted runner from the repository root:

```powershell
docker build --tag vericode-runner:day2 sandbox
.\.venv\Scripts\python.exe -m pytest --run-docker -q -p no:cacheprovider tests/test_docker_executor.py
```

The build context allowlists four runner files; it excludes tasks, evaluation data,
the repository, environments, and credentials. The official Python 3.13.5 base
manifest is pinned to a digest, and Linux pytest dependencies are version-pinned.
Build-time dependency downloads need network access. Execution does not pull
images: a trusted local image is resolved to an immutable image ID for each job.
Rebuild the image whenever the trusted harness changes. Preflight allowlists the
public base-image environment names; inspection rejects additional variables
(including Docker proxy injection), altered harness arguments, and persistent
logging. Candidate processes receive only a fixed environment plus pytest's own
version/current-test metadata.
A version label (`io.vericode.runner=2`) rejects earlier harnesses without the
independent deadline. It identifies compatibility but does not authenticate an image;
only use images you built from trusted source.

Each job receives bounded JSON containing source, visible tests, and a protocol
token over stdin. The image's parent harness writes source/tests into `/workspace`
and launches pytest as a separate child with a fixed environment. It never imports
candidate modules itself. No repository, home, Docker socket, credential file,
or host directory is mounted. The runner does not load evaluator data.

Defaults: 0.5 CPU, 256 MiB RAM with memory+swap equal to RAM, 32 PIDs, 10 seconds
of attached execution, 16 MiB workspace, 8 MiB temporary storage, and 16 KiB
captured output. There are also nofile, core, file-size, inode, and shared-memory
limits. Root filesystem is read-only; writable workspace/tmp are `noexec`,
`nosuid`, `nodev` tmpfs mounts. Python can still interpret text on a `noexec` mount.
User is 65532:65532, capabilities are dropped, and no-new-privileges is enabled.
Docker policy is inspected before starting any candidate.

The host watchdog bounds the attached execution phase, not image building or the
whole preflight/create/cleanup lifecycle. Control commands have five-second
deadlines. On timeout/output overflow the client is killed and the container is
force-removed, terminating the entire container job, including descendants.
An independent Linux timer in the trusted parent harness starts before input is
read. It exits with code 124 on deadline; stopping the container's main process
causes the runtime to terminate its descendants. The host records that as timeout
and still verifies/removes the job. A live check extends the host deadline to
verify the container timer independently, including a spawned child.
Cleanup is verified via the exact generated job name. A daemon failure can prevent
cleanup confirmation; that is an infrastructure error with the job name retained
for recovery. That executor blocks further jobs after an unconfirmed cleanup.
Only this invocation's container is removed. A new CLI process cannot infer a
previous process's unconfirmed cleanup, so resolve a reported job before resuming.

The controller drains output while retaining a bounded prefix. Decoded UTF-8 text
also obeys the byte cap, including replacement of invalid binary output. The harness emits
a structured outcome with a per-job token after pytest exits. Missing/malformed
reports, ambiguous result frames, and unexpected exits cannot count as success.
Skipped tests or an empty suite cannot count as a passing suite. Exceptions during
test execution, collection errors, timeouts, OOM, and infrastructure errors are
distinct statuses. Candidate output remains untrusted text.

The pytest child and candidate run in the same Python process and share a writable
workspace. Deliberately malicious Python could tamper with pytest or its XML
report. The protocol and count checks catch missing/ambiguous reports, not every
possible attempt to falsify test outcomes. These outcomes are evidence for local
repair research, not an adversarial correctness certificate. Container isolation
reduces risk without guaranteeing host security. Do not expose this runner as a
public arbitrary-code execution service.

## Verified engineering checks, 2026-10-11

Test environment: Windows, Docker Desktop 29.7.2, WSL2 Linux 6.6.87.2, cgroup v2.
The evidence is trusted fixture execution and controller tests, not an escape
audit or a live-model experiment. Full report is saved locally as
`artifacts/day2-final-checks.xml` and is reproducible with `pytest --run-docker`.
The final suite passed 104 host-side checks, including 17 Docker integration
checks; pytest workers inside these jobs also run the specified fixture cases.

| Control | Evidence |
| --- | --- |
| Non-root and reduced privileges | UID/GID 65532, effective/permitted/bounding capabilities zero, no-new-privileges=1, seccomp=2 inside worker |
| Network denial | Only loopback interface; numeric external TCP connection denied; inspected network mode is none |
| Host/evaluator separation | Fake host credentials absent from worker and parent; sentinel host/evaluation files and repository/controller paths absent; no directory binds/socket |
| Read-only root and bounded mounts | Base write rejected; workspace/tmp mount flags and 16/8 MiB capacities observed; workspace filling rejected with ENOSPC |
| CPU/memory/PID settings | Worker reads quota ratio 0.5, 256 MiB memory, zero swap, and 32-PID cap from cgroup v2 |
| Resource exhaustion | Bounded process spawning rejected with EAGAIN; oversized allocation reported as Docker OOM/resource limit |
| Time and output | Host and independent container deadlines remove jobs with descendants; ASCII/binary floods stop at bounded output |
| Cleanup and dataset preservation | Jobs absent after completion/failure/timeout; source fixture bytes unchanged despite container workspace writes; simulated cleanup failure blocks subsequent submissions |
| Result integrity checks | Empty/skipped suites, early exit without report, ambiguous/token-mismatched frames, and relaxed inspected policies are rejected |

CPU quota settings were observed, not benchmarked for sustained throughput under
all scheduler loads. The parent and child share a UID, and malicious Python may
interfere with parent signals or pytest/report files. The host watchdog is a
separate control, but controller/runtime failure or host/VM suspension can delay
enforcement and cleanup. A new process does not automatically recover old jobs.
Kernel/container escape resistance and other Docker/OS versions are unverified.

References: [Docker runtime flags](https://docs.docker.com/reference/cli/docker/container/run/),
[resource limits](https://docs.docker.com/engine/containers/resource_constraints/),
and [tmpfs behaviour](https://docs.docker.com/engine/storage/tmpfs/). Docker documents
that tmpfs is temporary storage and counts toward the memory limit; swap and
underlying host storage remain part of the trusted infrastructure.
