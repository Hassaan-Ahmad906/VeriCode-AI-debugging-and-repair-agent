import json

import pytest

from vericode.docker_executor import DockerExecutor, SandboxUnavailable
from vericode.processes import ProcessResult
from vericode.sandbox_policy import ExecutionLimits, create_arguments
from vericode.schemas import ValidationError


@pytest.mark.parametrize("field,value", [
    ("wall_seconds", 0), ("wall_seconds", float("nan")), ("cpus", 50),
    ("memory_bytes", True), ("pids", 0), ("output_bytes", 100_000),
])
def test_unsafe_limits_rejected(field, value):
    with pytest.raises(ValidationError, match=field):
        ExecutionLimits(**{field: value})


def test_no_mounts_or_credentials_in_docker_arguments(monkeypatch):
    monkeypatch.setenv("VERICODE_API_KEY", "credential-sentinel")
    args = create_arguments("vericode-job-test", "sha256:" + "a" * 64, ExecutionLimits())
    assert not any(argument in ("-v", "--volume", "--mount", "--env", "-e", "--env-file") for argument in args)
    assert "credential-sentinel" not in " ".join(args)
    assert "--network=none" in args and "--user=65532:65532" in args
    assert "--read-only" in args and "--cap-drop=ALL" in args


def test_missing_docker_returns_error_without_host_fallback(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("docker unavailable")

    monkeypatch.setattr("vericode.docker_executor.run_bounded", missing)
    result = DockerExecutor().run("def f(): return 1", "def test_f(): assert True")
    assert result.status == "infrastructure_error"
    assert result.tests_passed is None
    assert result.cleanup_confirmed is None


def test_forged_or_duplicate_output_frames_are_rejected():
    runner = DockerExecutor()
    fake = b'VERICODE_RESULT={"status":"passed","protocol":"wrong"}\n'
    with pytest.raises(ValidationError, match="protocol"):
        runner._decode(fake, "expected")
    with pytest.raises(ValidationError, match="ambiguous"):
        runner._decode(fake + fake, "expected")


def test_preflight_rejects_old_image_without_independent_deadline(monkeypatch):
    info = {"OSType": "linux", "CgroupVersion": "2", "MemoryLimit": True,
            "SwapLimit": True, "CpuCfsQuota": True, "PidsLimit": True,
            "SecurityOptions": ["name=seccomp,profile=builtin"]}
    old_image = {"Os": "linux", "Config": {"Labels": {"io.vericode.runner": "1"}}}
    runner = DockerExecutor()

    def control(*args, **kwargs):
        return ProcessResult(0, json.dumps(info if args[0] == "info" else [old_image]).encode())

    monkeypatch.setattr(runner, "_control", control)
    with pytest.raises(SandboxUnavailable, match="trusted VeriCode runner image"):
        runner.prepare()
    assert runner.image_id is None


@pytest.mark.docker
def test_docker_normal_completion(docker_executor):
    result = docker_executor.run("def add(a, b): return a + b", "from solution import add\ndef test_add(): assert add(2, 3) == 5")
    assert result.status == "passed", result
    assert result.tests_passed == 1 and result.tests_failed == 0
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_docker_exception_is_test_failure(docker_executor):
    result = docker_executor.run("def f(): raise ValueError('trusted exception fixture')", "from solution import f\ndef test_f(): assert f() == 1")
    assert result.status == "failed", result
    assert result.tests_failed == 1
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_docker_collection_exception_is_separate(docker_executor):
    result = docker_executor.run("raise ValueError('trusted collection fixture')", "from solution import f\ndef test_f(): assert f() == 1")
    assert result.status == "test_error", result
    assert result.tests_errors == 1
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_docker_timeout_removes_full_job(docker_executor):
    docker_executor.limits = ExecutionLimits(wall_seconds=2)
    result = docker_executor.run("def f():\n    while True: pass", "from solution import f\ndef test_f(): f()")
    assert result.status == "timeout", result
    assert result.tests_passed is None
    assert result.cleanup_confirmed is True


def test_cleanup_failure_blocks_next_job(monkeypatch):
    limits = ExecutionLimits()
    image_id = "sha256:" + "a" * 64
    runner = DockerExecutor(limits=limits)
    events = []
    policy = {
        "Image": image_id,
        "Config": {"User": "65532:65532", "Volumes": None, "Env": [],
                   "Entrypoint": ["/usr/local/bin/python"], "Cmd": ["-I", "-B", "/opt/vericode/runner.py", "10.0"],
                   "WorkingDir": "/workspace"},
        "HostConfig": {
            "NetworkMode": "none", "ReadonlyRootfs": True, "Privileged": False,
            "Memory": limits.memory_bytes, "MemorySwap": limits.memory_bytes,
            "NanoCpus": 500_000_000, "PidsLimit": limits.pids, "IpcMode": "private",
            "CgroupnsMode": "private", "Init": True, "Tmpfs": limits.tmpfs(),
            "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"],
            "LogConfig": {"Type": "none"},
        },
        "State": {"ExitCode": 0, "Running": False, "OOMKilled": False},
    }

    def control(*args, **kwargs):
        events.append(args[0])
        return ProcessResult(0, json.dumps([policy]).encode() if args[0] == "inspect" else b"created")

    def attached(*args, **kwargs):
        events.append("start")
        token = json.loads(kwargs["input_bytes"])["protocol"]
        frame = {"protocol": token, "status": "passed", "tests_passed": 1,
                 "tests_failed": 0, "tests_errors": 0, "tests_skipped": 0, "exit_code": 0}
        return ProcessResult(0, b"VERICODE_RESULT=" + json.dumps(frame).encode())

    monkeypatch.setattr(runner, "prepare", lambda: image_id)
    monkeypatch.setattr(runner, "_control", control)
    monkeypatch.setattr(runner, "_cleanup", lambda name: False)
    monkeypatch.setattr("vericode.docker_executor.run_bounded", attached)
    result = runner.run("def f(): return 1", "def test_f(): assert True")
    assert result.status == "infrastructure_error"
    assert result.tests_passed is None and result.cleanup_confirmed is False
    assert result.job_name in result.detail
    before = list(events)
    blocked = runner.run("def f(): return 1", "def test_f(): assert True")
    assert blocked.status == "infrastructure_error"
    assert events == before


@pytest.mark.docker
def test_docker_output_flood_is_bounded_and_job_removed(docker_executor):
    result = docker_executor.run(
        "def f():\n    while True: print('x' * 4096, flush=True)",
        "from solution import f\ndef test_f(): f()",
    )
    assert result.status == "output_limit", result
    assert result.output_truncated is True
    assert len(result.output.encode("utf-8")) <= docker_executor.limits.output_bytes
    assert result.tests_passed is None and result.cleanup_confirmed is True


@pytest.mark.docker
def test_timeout_removes_job_with_spawned_descendant(docker_executor):
    docker_executor.limits = ExecutionLimits(wall_seconds=2)
    source = (
        "import subprocess, sys, time\n"
        "def f():\n"
        "    subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "    while True: time.sleep(1)\n"
    )
    result = docker_executor.run(source, "from solution import f\ndef test_f(): f()")
    assert result.status == "timeout", result
    assert result.cleanup_confirmed is True


@pytest.mark.docker
@pytest.mark.parametrize("tests", ["# no tests", "import pytest\n@pytest.mark.skip(reason='fixture')\ndef test_skipped(): pass"], ids=["empty-suite", "skipped-suite"])
def test_empty_or_skipped_suite_does_not_pass(docker_executor, tests):
    result = docker_executor.run("def f(): return 1", tests)
    assert result.status == "test_error", result
    assert result.tests_passed == 0
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_early_success_exit_without_report_does_not_pass(docker_executor):
    result = docker_executor.run("import os\nos._exit(0)", "from solution import f\ndef test_f(): f()")
    assert result.status == "infrastructure_error", result
    assert result.tests_passed is None
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_container_watchdog_works_when_host_deadline_is_extended(docker_executor, monkeypatch):
    from vericode.processes import run_bounded

    docker_executor.limits = ExecutionLimits(wall_seconds=1)

    def delayed_host(command, **kwargs):
        if command[:2] == ["docker", "start"]:
            kwargs["timeout"] = 30
        return run_bounded(command, **kwargs)

    monkeypatch.setattr("vericode.docker_executor.run_bounded", delayed_host)
    source = (
        "import subprocess, sys\n"
        "def f():\n"
        "    subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "    while True: pass\n"
    )
    result = docker_executor.run(source, "from solution import f\ndef test_f(): f()")
    assert result.status == "timeout", result
    assert result.exit_code == 124
    assert "container watchdog" in result.detail
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_binary_output_is_bounded_after_utf8_replacement(docker_executor):
    result = docker_executor.run(
        "import os\ndef f(): os.write(1, bytes([255]) * 65536)",
        "from solution import f\ndef test_f(): f()",
    )
    assert result.status == "output_limit", result
    assert result.output_truncated is True
    assert len(result.output.encode("utf-8")) <= docker_executor.limits.output_bytes
    assert result.cleanup_confirmed is True
