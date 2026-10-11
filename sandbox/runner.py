"""Trusted image entry point. Candidate/test imports occur only in its child."""

import json
from pathlib import Path
import stat
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

MAX_PAYLOAD = 262_144
MAX_REPORT = 32_768


def read_report(path, returncode):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > MAX_REPORT:
        raise ValueError("missing, oversized, or non-regular pytest report")
    root = ET.fromstring(path.read_bytes())
    suites = list(root.iter("testsuite"))
    if not suites:
        raise ValueError("pytest report has no test suites")
    totals = {key: sum(int(suite.attrib.get(key, "0")) for suite in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    passed = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    if min(*totals.values(), passed) < 0:
        raise ValueError("invalid pytest report counts")
    if returncode == 0 and totals["tests"] > 0 and not any(totals[key] for key in ("failures", "errors", "skipped")):
        status = "passed"
    elif returncode == 1 and totals["failures"] > 0:
        status = "failed"
    elif returncode in (0, 2, 5):
        status = "test_error"
    else:
        raise ValueError("pytest exit code and report disagree")
    return dict(status=status, tests_passed=passed, tests_failed=totals["failures"],
                tests_errors=totals["errors"], tests_skipped=totals["skipped"],
                exit_code=returncode)


def main():
    protocol = None
    try:
        raw = sys.stdin.buffer.read(MAX_PAYLOAD + 1)
        if len(raw) > MAX_PAYLOAD:
            raise ValueError("execution input exceeds limit")
        payload = json.loads(raw)
        if set(payload) != {"source", "tests", "protocol"}:
            raise ValueError("invalid execution payload fields")
        protocol = payload["protocol"]
        for field in ("source", "tests"):
            if not isinstance(payload[field], str) or len(payload[field].encode("utf-8")) > 32_768:
                raise ValueError("invalid execution source/test size")
        workspace = Path("/workspace")
        (workspace / "solution.py").write_text(payload["source"], encoding="utf-8")
        (workspace / "test_visible.py").write_text(payload["tests"], encoding="utf-8")
        report = workspace / f"report-{uuid4().hex}.xml"
        # Explicit env: no inherited credentials or arbitrary pytest configuration.
        environment = {
            "PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/nonexistent",
            "LANG": "C.UTF-8", "TMPDIR": "/tmp", "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
        child = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "-q", "-s", "--tb=short",
             "--noconftest", "-p", "no:cacheprovider", "-c", "/opt/vericode/pytest.ini",
             f"--junitxml={report}", "/workspace/test_visible.py"],
            cwd=workspace, env=environment, stdin=subprocess.DEVNULL, check=False,
        )
        result = read_report(report, child.returncode)
    except Exception:
        # Do not emit attacker-controlled exception text into the result frame.
        result = {"status": "infrastructure_error", "detail": "Runner could not obtain a valid pytest report."}
    result["protocol"] = protocol
    print("\nVERICODE_RESULT=" + json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
