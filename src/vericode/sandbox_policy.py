"""Validated limits and fixed Docker arguments for an untrusted execution job."""

from dataclasses import dataclass
import math
import re
from typing import Any

from vericode.schemas import ValidationError

DEFAULT_IMAGE = "vericode-runner:day2"
RUNNER_LABEL = "io.vericode.runner"


@dataclass(frozen=True)
class ExecutionLimits:
    wall_seconds: float = 10.0
    cpus: float = 0.5
    memory_bytes: int = 256 * 1024 * 1024
    pids: int = 32
    workspace_bytes: int = 16 * 1024 * 1024
    temporary_bytes: int = 8 * 1024 * 1024
    output_bytes: int = 16 * 1024

    def __post_init__(self) -> None:
        for field, minimum, maximum in (
            ("wall_seconds", 0.5, 60), ("cpus", 0.1, 2),
            ("memory_bytes", 64 * 1024 * 1024, 1024 * 1024 * 1024),
            ("pids", 8, 128), ("workspace_bytes", 1024 * 1024, 64 * 1024 * 1024),
            ("temporary_bytes", 1024 * 1024, 32 * 1024 * 1024),
            ("output_bytes", 1024, 16 * 1024),
        ):
            value = getattr(self, field)
            expected = (int, float) if field in ("wall_seconds", "cpus") else (int,)
            if type(value) not in expected or not math.isfinite(value) or not minimum <= value <= maximum:
                raise ValidationError(f"{field}: expected a finite value in [{minimum}, {maximum}]")

    def tmpfs(self) -> dict[str, str]:
        options = "rw,noexec,nosuid,nodev,nr_inodes=1024,mode=0700,uid=65532,gid=65532"
        return {
            "/workspace": f"{options},size={self.workspace_bytes}",
            "/tmp": f"{options},size={self.temporary_bytes}",
        }


def validate_image_name(image: str) -> None:
    if not isinstance(image, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:/@-]{0,199}", image):
        raise ValidationError("image: expected one Docker image reference, not CLI options")


def create_arguments(name: str, image_id: str, limits: ExecutionLimits) -> list[str]:
    args = [
        "create", "--name", name, "--label", f"{RUNNER_LABEL}=1", "--pull=never",
        "--interactive", "--init", "--network=none", "--user=65532:65532",
        "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--cpus", str(limits.cpus), "--memory", str(limits.memory_bytes),
        "--memory-swap", str(limits.memory_bytes), "--pids-limit", str(limits.pids),
        "--ulimit", "nofile=64:64", "--ulimit", "core=0:0",
        "--ulimit", "fsize=1048576:1048576", "--shm-size=1048576",
        "--ipc=private", "--cgroupns=private", "--hostname=vericode-job",
        "--log-driver=none", "--restart=no", "--workdir=/workspace",
        "--entrypoint=/usr/local/bin/python",
    ]
    for path, options in limits.tmpfs().items():
        args.extend(["--tmpfs", f"{path}:{options}"])
    return args + [image_id, "-I", "-B", "/opt/vericode/runner.py"]


def verify_container(data: dict[str, Any], image_id: str, limits: ExecutionLimits) -> None:
    """Fail closed before starting a container whose inspected policy differs."""
    host = data["HostConfig"]
    config = data["Config"]
    required = {
        "NetworkMode": "none", "ReadonlyRootfs": True, "Privileged": False,
        "Memory": limits.memory_bytes, "MemorySwap": limits.memory_bytes,
        "NanoCpus": round(limits.cpus * 1_000_000_000), "PidsLimit": limits.pids,
        "IpcMode": "private", "CgroupnsMode": "private", "Init": True,
        "Tmpfs": limits.tmpfs(),
    }
    if any(host.get(key) != value for key, value in required.items()):
        raise ValidationError("container inspection does not match required execution limits")
    if config.get("User") != "65532:65532" or data.get("Image") != image_id:
        raise ValidationError("container user/image differs from the approved configuration")
    if host.get("CapDrop") != ["ALL"] or "no-new-privileges" not in host.get("SecurityOpt", []):
        raise ValidationError("container privilege restrictions are missing")
    if host.get("Binds") or host.get("Devices") or host.get("DeviceRequests") or host.get("VolumesFrom"):
        raise ValidationError("host mounts and devices are forbidden")
    if any(mount.get("Type") != "tmpfs" for mount in data.get("Mounts", [])):
        raise ValidationError("only bounded tmpfs mounts are permitted")
    if config.get("Volumes") or host.get("PortBindings") or host.get("PidMode") == "host":
        raise ValidationError("volumes, exposed ports, and host PID sharing are forbidden")
