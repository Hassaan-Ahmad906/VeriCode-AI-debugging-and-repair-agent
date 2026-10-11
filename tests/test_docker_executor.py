import pytest

from vericode.docker_executor import DockerExecutor
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
