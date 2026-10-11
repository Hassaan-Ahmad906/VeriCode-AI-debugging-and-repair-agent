"""Bounded controller subprocesses. Never use this to execute candidate Python."""

from dataclasses import dataclass
import subprocess
from threading import Event, Thread
from time import monotonic, sleep
from collections.abc import Sequence


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    output: bytes
    stop_reason: str | None = None


def run_bounded(
    command: Sequence[str], *, timeout: float, output_limit: int,
    input_bytes: bytes | None = None,
) -> ProcessResult:
    """Drain merged output continuously; retain at most output_limit bytes."""
    process = subprocess.Popen(
        list(command), stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    output = bytearray()
    overflow = Event()
    reader_done = Event()

    def read_output() -> None:
        try:
            assert process.stdout is not None
            while chunk := process.stdout.read1(4096):
                remaining = output_limit - len(output)
                output.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    overflow.set()
        finally:
            reader_done.set()

    def write_input() -> None:
        assert process.stdin is not None
        try:
            process.stdin.write(input_bytes or b"")
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            process.stdin.close()

    reader = Thread(target=read_output, daemon=True)
    reader.start()
    writer = None
    if input_bytes is not None:
        writer = Thread(target=write_input, daemon=True)
        writer.start()
    deadline = monotonic() + timeout
    stop_reason = None
    try:
        while True:
            if overflow.is_set():
                stop_reason = "output_limit"
                break
            if process.poll() is not None and reader_done.is_set():
                break
            if monotonic() >= deadline:
                stop_reason = "timeout"
                break
            sleep(0.01)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=2)
        reader.join(timeout=1)
        if writer is not None:
            writer.join(timeout=1)
        if reader_done.is_set() and process.stdout is not None:
            process.stdout.close()
    return ProcessResult(process.returncode, bytes(output), stop_reason)
