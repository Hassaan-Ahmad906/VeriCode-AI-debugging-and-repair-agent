# Local Docker execution

The mock demo remains the default. Candidate and test Python may run only through
`DockerExecutor`; there is no host execution fallback. Requires a local Linux
Docker daemon with memory/swap, CPU quota, PID limits, and default seccomp enabled.

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
A label identifies the intended harness but does not authenticate an image;
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

The watchdog bounds the attached execution phase, not image building or the
whole preflight/create/cleanup lifecycle. Control commands have five-second
deadlines. On timeout/output overflow the client is killed and the container is
force-removed, terminating the entire container job, including descendants.
Cleanup is verified via the exact generated job name. A daemon failure can prevent
cleanup confirmation; that is an infrastructure error with the job name retained
for recovery. Only this invocation's container is removed.

The controller drains output while retaining a bounded prefix. The harness emits
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

References: [Docker runtime flags](https://docs.docker.com/reference/cli/docker/container/run/),
[resource limits](https://docs.docker.com/engine/containers/resource_constraints/),
and [tmpfs behaviour](https://docs.docker.com/engine/storage/tmpfs/). Docker documents
that tmpfs is temporary storage and counts toward the memory limit; swap and
underlying host storage remain part of the trusted infrastructure.
