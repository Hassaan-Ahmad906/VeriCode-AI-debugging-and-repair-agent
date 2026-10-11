from copy import deepcopy
import textwrap

import pytest

from vericode.sandbox_policy import ExecutionLimits, verify_container
from vericode.schemas import ValidationError


def inspected_policy():
    limits = ExecutionLimits()
    return {
        "Image": "sha256:" + "a" * 64,
        "Config": {"User": "65532:65532", "Volumes": None, "Env": ["PATH=/usr/bin"],
                   "Entrypoint": ["/usr/local/bin/python"], "Cmd": ["-I", "-B", "/opt/vericode/runner.py", "10.0"],
                   "WorkingDir": "/workspace"},
        "HostConfig": {
            "NetworkMode": "none", "ReadonlyRootfs": True, "Privileged": False,
            "Memory": limits.memory_bytes, "MemorySwap": limits.memory_bytes,
            "NanoCpus": 500_000_000, "PidsLimit": limits.pids, "IpcMode": "private",
            "CgroupnsMode": "private", "Init": True, "Tmpfs": limits.tmpfs(),
            "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"], "LogConfig": {"Type": "none"},
        }, "Mounts": [],
    }


@pytest.mark.parametrize("section,key,value", [
    ("HostConfig", "NetworkMode", "host"),
    ("HostConfig", "ReadonlyRootfs", False),
    ("HostConfig", "Privileged", True),
    ("HostConfig", "Binds", ["C:/Users/User:/host"]),
    ("HostConfig", "Devices", [{"PathOnHost": "/dev/test"}]),
    ("HostConfig", "PidMode", "host"),
    ("HostConfig", "PidsLimit", 0),
    ("HostConfig", "SecurityOpt", []),
    ("HostConfig", "CapDrop", []),
    ("HostConfig", "LogConfig", {"Type": "json-file"}),
    ("Config", "User", "0"),
    ("Config", "Env", ["PATH=/usr/bin", "VERICODE_API_KEY=not-a-real-key"]),
    ("Config", "Entrypoint", ["/bin/sh"]),
])
def test_inspection_rejects_relaxed_or_injected_policy(section, key, value):
    data = deepcopy(inspected_policy())
    data[section][key] = value
    with pytest.raises(ValidationError):
        verify_container(data, data["Image"], ExecutionLimits(), ("PATH=/usr/bin",))


def test_inspection_rejects_unintended_volume():
    data = inspected_policy()
    data["Mounts"] = [{"Type": "bind", "Destination": "/host"}]
    with pytest.raises(ValidationError, match="tmpfs"):
        verify_container(data, data["Image"], ExecutionLimits(), ("PATH=/usr/bin",))


@pytest.mark.docker
def test_live_identity_network_resources_and_absence_of_host_assets(docker_executor, tmp_path, monkeypatch):
    sentinel = "vericode-host-credential-sentinel"
    monkeypatch.setenv("VERICODE_API_KEY", sentinel)
    monkeypatch.setenv("OPENAI_API_KEY", sentinel)
    host_file = tmp_path / "host-only-sentinel.txt"
    host_file.write_text("host-only-fixture", encoding="utf-8")
    evaluation = tmp_path / "evaluation_assets"
    evaluation.mkdir()
    (evaluation / "suite.py").write_text("host-only-evaluator-fixture", encoding="utf-8")
    host_paths = [str(host_file), str(evaluation)]
    for path in (host_file, evaluation):
        posix = path.as_posix()
        if len(posix) > 2 and posix[1] == ":":
            relative = posix[2:].lstrip("/")
            host_paths += [f"/mnt/{posix[0].lower()}/{relative}", f"/run/desktop/mnt/host/{posix[0].lower()}/{relative}"]
    tests = textwrap.dedent('''
        import errno, os, resource, socket
        from pathlib import Path
        import pytest
        from solution import marker

        def status():
            return dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)

        def test_non_root_identity():
            assert marker() == 'inside the job'
            assert os.getuid() == 65532 and os.getgid() == 65532

        def test_privileges_and_seccomp():
            fields = status()
            assert all(int(fields[key].strip(), 16) == 0 for key in ('CapEff', 'CapPrm', 'CapBnd'))
            assert fields['NoNewPrivs'].strip() == '1'
            assert fields['Seccomp'].strip() == '2'

        def test_no_host_credentials():
            assert set(os.environ) == {'PATH', 'HOME', 'LANG', 'TMPDIR', 'PYTHONDONTWRITEBYTECODE', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD', 'PYTEST_CURRENT_TEST', 'PYTEST_VERSION'}
            parent = Path(f'/proc/{os.getppid()}/environ').read_bytes()
            if b'vericode-host-credential-sentinel' in parent:
                raise AssertionError('host credential reached the parent harness')

        def test_no_host_files():
            assert all(not Path(path).exists() for path in HOST_PATHS)

        def test_no_evaluator_or_controller_workspace():
            assert {path.name for path in Path('/workspace').iterdir()} == {'solution.py', 'test_visible.py'}
            assert {path.name for path in Path('/opt/vericode').iterdir()} == {'runner.py', 'pytest.ini', 'requirements.txt'}
            assert not Path('/workspace/data/evaluation').exists()
            assert not Path('/data/evaluation').exists()
            assert not Path('/workspace/src/vericode/docker_executor.py').exists()

        def test_readonly_base_and_no_docker_socket():
            with pytest.raises(OSError):
                Path('/opt/vericode/must-not-write').write_text('denied')
            assert not Path('/var/run/docker.sock').exists()
            assert not Path('/run/docker.sock').exists()
            assert os.environ['HOME'] == '/nonexistent'

        def test_network_disabled():
            assert {name for _, name in socket.if_nameindex()} == {'lo'}
            with socket.socket() as connection:
                connection.settimeout(0.25)
                with pytest.raises(OSError):
                    connection.connect(('1.1.1.1', 443))

        def test_resource_limits():
            cgroup = Path('/sys/fs/cgroup')
            assert int((cgroup / 'memory.max').read_text()) == 268435456
            assert int((cgroup / 'memory.swap.max').read_text()) == 0
            assert int((cgroup / 'pids.max').read_text()) == 32
            quota, period = map(int, (cgroup / 'cpu.max').read_text().split())
            assert quota / period == 0.5
            assert resource.getrlimit(resource.RLIMIT_NOFILE) == (64, 64)
            assert resource.getrlimit(resource.RLIMIT_FSIZE) == (1048576, 1048576)
            assert resource.getrlimit(resource.RLIMIT_CORE) == (0, 0)

        def test_bounded_temporary_mounts():
            mounts = [line.split() for line in Path('/proc/mounts').read_text().splitlines()]
            for path, size in (('/workspace', 16777216), ('/tmp', 8388608)):
                row = next(row for row in mounts if row[1] == path)
                assert row[2] == 'tmpfs'
                assert {'noexec', 'nosuid', 'nodev'} <= set(row[3].split(','))
                fs = os.statvfs(path)
                assert fs.f_blocks * fs.f_frsize == size
    ''')
    tests = "HOST_PATHS = " + repr(host_paths) + "\n" + tests
    result = docker_executor.run("def marker(): return 'inside the job'", tests)
    assert result.status == "passed", f"{result.detail}\n{result.output}\ncleanup={result.cleanup_confirmed}"
    assert result.tests_passed == 9
    assert result.cleanup_confirmed is True
    assert host_file.read_text(encoding="utf-8") == "host-only-fixture"
    assert (evaluation / "suite.py").read_text(encoding="utf-8") == "host-only-evaluator-fixture"


@pytest.mark.docker
def test_pid_limit_rejects_excess_processes(docker_executor):
    tests = textwrap.dedent('''
        import errno, subprocess
        def test_pid_cap():
            children = []
            rejected = False
            try:
                for _ in range(40):
                    try:
                        children.append(subprocess.Popen(['/bin/sleep', '30']))
                    except OSError as exc:
                        assert exc.errno == errno.EAGAIN
                        rejected = True
                        break
                assert rejected
            finally:
                for child in children:
                    child.terminate()
                for child in children:
                    child.wait(timeout=2)
    ''')
    result = docker_executor.run("def marker(): return 1", tests)
    assert result.status == "passed", result
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_workspace_capacity_is_enforced(docker_executor):
    tests = textwrap.dedent('''
        import errno
        from pathlib import Path
        def test_workspace_cap():
            paths = []
            exhausted = False
            try:
                for index in range(64):
                    path = Path(f'/workspace/fill-{index}')
                    paths.append(path)
                    try:
                        path.write_bytes(b'x' * (512 * 1024))
                    except OSError as exc:
                        assert exc.errno == errno.ENOSPC
                        exhausted = True
                        break
                assert exhausted
            finally:
                for path in paths:
                    path.unlink(missing_ok=True)
    ''')
    result = docker_executor.run("def marker(): return 1", tests)
    assert result.status == "passed", result
    assert result.cleanup_confirmed is True


@pytest.mark.docker
def test_oom_is_reported_separately(docker_executor):
    result = docker_executor.run(
        "def f():\n    data = bytearray(400 * 1024 * 1024)\n    return len(data)",
        "from solution import f\ndef test_memory_cap(): f()",
    )
    assert result.status == "resource_limit", result
    assert result.tests_passed is None
    assert result.cleanup_confirmed is True
