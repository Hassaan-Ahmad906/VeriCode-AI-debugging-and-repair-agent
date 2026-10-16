"""Start the optional UI on loopback only, with no browser side effects."""

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="VeriCode local interface")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    if importlib.util.find_spec("streamlit") is None:
        parser.error('install the optional UI: python -m pip install -e ".[ui]"')
    return subprocess.call([
        sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("ui.py")),
        "--server.address=127.0.0.1", f"--server.port={args.port}",
        "--server.headless=true", "--browser.gatherUsageStats=false",
        "--theme.base=dark", "--theme.primaryColor=#818cf8",
        "--theme.backgroundColor=#0b0d12", "--theme.secondaryBackgroundColor=#141720",
        "--theme.textColor=#e4e7ef",
        "--server.fileWatcherType=none", "--", "--data-root", str(args.data_root.resolve()),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
