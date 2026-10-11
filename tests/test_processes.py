import sys

from vericode.processes import run_bounded


def test_controller_output_capture_is_bounded():
    # This is trusted test-harness code, not candidate code or user-supplied text.
    result = run_bounded(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 200000); sys.stdout.flush()"],
        timeout=5, output_limit=2048,
    )
    assert result.stop_reason == "output_limit"
    assert len(result.output) == 2048


def test_controller_process_timeout_is_bounded():
    result = run_bounded([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.2, output_limit=2048)
    assert result.stop_reason == "timeout"
    assert result.returncode != 0


def test_input_and_short_output_complete_normally():
    result = run_bounded(
        [sys.executable, "-c", "import sys; print(sys.stdin.buffer.read().decode())"],
        input_bytes=b"trusted harness input", timeout=5, output_limit=2048,
    )
    assert result.stop_reason is None
    assert result.returncode == 0
    assert result.output.strip() == b"trusted harness input"
