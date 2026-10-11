"""Docker-only candidate execution; failures never fall back to host Python."""

from dataclasses import replace
import json
import re
from time import monotonic
from uuid import uuid4

from vericode.processes import ProcessResult, run_bounded
from vericode.results import ExecutionResult
from vericode.sandbox_policy import (
    DEFAULT_IMAGE, RUNNER_LABEL, RUNNER_VERSION, ExecutionLimits, create_arguments,
    validate_image_name, verify_container,
)
from vericode.schemas import ValidationError, require_text


class SandboxUnavailable(RuntimeError):
    """A required Docker capability or trusted local image is missing."""


class DockerExecutor:
    def __init__(self, image: str = DEFAULT_IMAGE, limits: ExecutionLimits | None = None):
        validate_image_name(image)
        self.image = image
        self.limits = limits or ExecutionLimits()
        self.image_id: str | None = None
        self.blocked_job: str | None = None
        self.image_environment: tuple[str, ...] = ()

    def _control(self, *arguments: str, check: bool = True) -> ProcessResult:
        result = run_bounded(["docker", *arguments], timeout=5, output_limit=65_536)
        if result.stop_reason or (check and result.returncode != 0):
            raise SandboxUnavailable(f"Docker {arguments[0]} failed; check daemon access and the local runner image.")
        return result

    def prepare(self) -> str:
        try:
            info = json.loads(self._control("info", "--format", "{{json .}}").output)
            if info.get("OSType") != "linux" or info.get("CgroupVersion") != "2" or not all(
                info.get(key) is True for key in ("MemoryLimit", "SwapLimit", "CpuCfsQuota", "PidsLimit")
            ):
                raise SandboxUnavailable("Docker must support Linux cgroup v2 CPU, memory, swap, and PID limits.")
            if not any("name=seccomp" in option for option in info.get("SecurityOptions", [])):
                raise SandboxUnavailable("Docker's default seccomp protection is required.")
            image = json.loads(self._control("image", "inspect", self.image).output)[0]
            if (image.get("Os") != "linux" or image["Config"].get("Volumes")
                or (image["Config"].get("Labels") or {}).get(RUNNER_LABEL) != RUNNER_VERSION):
                raise SandboxUnavailable("Use the trusted VeriCode runner image without declared volumes.")
            image_id = image["Id"]
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", image_id):
                raise SandboxUnavailable("Docker did not return an immutable image ID.")
            environment = tuple(image["Config"].get("Env") or [])
            allowed = {"PATH", "LANG", "GPG_KEY", "PYTHON_VERSION", "PYTHON_SHA256"}
            if any(not isinstance(item, str) or item.partition("=")[0] not in allowed for item in environment):
                raise SandboxUnavailable("Runner image contains unexpected environment variables; rebuild the trusted image.")
            self.image_environment = environment
            self.image_id = image_id
            return image_id
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise SandboxUnavailable("Docker preflight failed; no candidate code was executed.") from exc

    def _cleanup(self, name: str) -> bool:
        try:
            self._control("rm", "--force", name, check=False)
            remaining = self._control("ps", "--all", "--filter", f"name=^{name}$", "--format", "{{.ID}}")
            return not remaining.output.strip()
        except (SandboxUnavailable, OSError):
            return False

    def _decode(self, raw: bytes, protocol: str) -> dict:
        frames = [line.removeprefix(b"VERICODE_RESULT=") for line in raw.splitlines()
                  if line.startswith(b"VERICODE_RESULT=")]
        if len(frames) != 1:
            raise ValidationError("missing or ambiguous container result frame")
        data = json.loads(frames[0])
        if data.pop("protocol", None) != protocol:
            raise ValidationError("container result frame has the wrong protocol token")
        if data.get("status") not in ("passed", "failed", "test_error", "infrastructure_error"):
            raise ValidationError("unexpected container result status")
        allowed = {"status", "tests_passed", "tests_failed", "tests_errors", "tests_skipped", "exit_code", "detail"}
        if data.keys() - allowed:
            raise ValidationError("container result frame contains unknown fields")
        if data["status"] != "infrastructure_error" and not {
            "tests_passed", "tests_failed", "tests_errors", "tests_skipped", "exit_code"
        } <= data.keys():
            raise ValidationError("container result frame is incomplete")
        if data["status"] != "infrastructure_error":
            if any(type(data[key]) is not int or data[key] < 0 for key in (
                "tests_passed", "tests_failed", "tests_errors", "tests_skipped"
            )):
                raise ValidationError("container test counts must be non-negative integers")
            permitted = {"passed": (0,), "failed": (1,), "test_error": (0, 2, 5)}
            if type(data["exit_code"]) is not int or data["exit_code"] not in permitted[data["status"]]:
                raise ValidationError("pytest exit code disagrees with reported outcome")
        return data

    def run(self, source: str, tests: str) -> ExecutionResult:
        require_text(source, "candidate source")
        require_text(tests, "visible tests")
        if self.blocked_job:
            return ExecutionResult("sandbox", "infrastructure_error", cleanup_confirmed=False,
                                   job_name=self.blocked_job,
                                   detail=f"Further execution blocked until cleanup of {self.blocked_job} is confirmed.")
        name = "vericode-job-" + uuid4().hex
        protocol = uuid4().hex
        started = monotonic()
        created = False
        cleaned = None
        output = ""
        truncated = False
        result = ExecutionResult("sandbox", "infrastructure_error", detail="Docker job did not start.")
        try:
            image_id = self.prepare()
            created = True  # Also clean up if create times out after the daemon creates the job.
            self._control(*create_arguments(name, image_id, self.limits))
            inspected = json.loads(self._control("inspect", name).output)[0]
            verify_container(inspected, image_id, self.limits, self.image_environment)
            payload = json.dumps({"source": source, "tests": tests, "protocol": protocol}, ensure_ascii=False).encode("utf-8")
            process = run_bounded(
                ["docker", "start", "--attach", "--interactive", name], input_bytes=payload,
                timeout=self.limits.wall_seconds, output_limit=self.limits.output_bytes,
            )
            output = process.output.decode("utf-8", errors="replace")
            encoded_output = output.encode("utf-8")
            output = encoded_output[:self.limits.output_bytes].decode("utf-8", errors="ignore")
            truncated = process.stop_reason == "output_limit" or len(encoded_output) > self.limits.output_bytes
            metadata = dict(output=output, output_truncated=truncated)
            if process.stop_reason:
                # Kill the whole job immediately; killing the attached CLI alone only detaches it.
                cleaned = self._cleanup(name)
                result = ExecutionResult("sandbox", process.stop_reason, detail=f"Execution stopped: {process.stop_reason}.", **metadata)
            else:
                state = json.loads(self._control("inspect", name).output)[0]["State"]
                if state.get("OOMKilled"):
                    result = ExecutionResult("sandbox", "resource_limit", exit_code=state.get("ExitCode"), detail="Docker reported an out-of-memory kill.", **metadata)
                elif state.get("ExitCode") == 124:
                    result = ExecutionResult("sandbox", "timeout", exit_code=124,
                                             detail="The trusted container watchdog reached its deadline.", **metadata)
                elif process.returncode != 0 or state.get("Running") or state.get("ExitCode") != 0:
                    result = ExecutionResult("sandbox", "infrastructure_error", exit_code=state.get("ExitCode"), detail="Container exited without a normal runner completion.", **metadata)
                else:
                    data = self._decode(process.output, protocol)
                    data.setdefault("detail", "Observed pytest outcome inside a constrained Docker container.")
                    result = ExecutionResult("sandbox", **data, **metadata)
        except (SandboxUnavailable, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            reason = str(exc) if isinstance(exc, (SandboxUnavailable, ValidationError)) else type(exc).__name__
            result = ExecutionResult("sandbox", "infrastructure_error", output=output, output_truncated=truncated,
                                     detail=f"Execution unavailable: {reason}; no host fallback.")
        finally:
            if created and cleaned is None:
                cleaned = self._cleanup(name)
        result = replace(result, duration_seconds=monotonic() - started,
                         cleanup_confirmed=cleaned, job_name=name if created else None, image_id=self.image_id)
        if cleaned is False:
            self.blocked_job = name
            result = replace(result, status="infrastructure_error", tests_passed=None, tests_failed=None,
                             tests_errors=None, tests_skipped=None,
                             detail=f"Cleanup could not be confirmed. Inspect Docker job {name} before further execution.")
        return result
