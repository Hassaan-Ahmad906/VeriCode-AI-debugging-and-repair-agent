"""Command-line entry point. All Day 1 operations are offline."""

import argparse
from collections.abc import Sequence
import json
from pathlib import Path

from vericode import __version__
from vericode.datasets import TaskManifest
from vericode.experiments import run_mock_demo, write_run
from vericode.schemas import ValidationError


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vericode",
        description="Local Python repair research; mock/offline operation by default.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    listing = commands.add_parser("list-tasks", help="validate and list development fixtures")
    listing.add_argument("--data-root", type=Path, default=Path("data"))
    demo = commands.add_parser("demo", help="run one offline MOCK demonstration (no code execution)")
    demo.add_argument("--task", default="clamp", help="development task ID (default: clamp)")
    demo.add_argument("--data-root", type=Path, default=Path("data"))
    demo.add_argument("--output", type=Path, help="new JSON artifact; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        if args.command == "list-tasks":
            manifest = TaskManifest.load(args.data_root / "manifests/development.json")
            for task in manifest.load_tasks(args.data_root / "repair"):
                print(f"{task.task_id}\t{task.split}\t{task.dataset_version}")
        elif args.command == "demo":
            record = run_mock_demo(args.data_root, args.task)
            if args.output:
                write_run(args.output, record)
            print(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False))
        else:
            parser.print_help()
    except (ValidationError, OSError) as exc:
        parser.exit(2, f"vericode: error: {exc}\n")
    return 0
