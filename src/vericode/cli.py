"""Local CLI: mock by default, explicit Docker execution for visible checks."""

import argparse
from dataclasses import asdict
from collections.abc import Sequence
import json
from pathlib import Path

from vericode import __version__
from vericode.datasets import TaskManifest
from vericode.experiments import run_mock_demo, write_run
from vericode.docker_executor import DockerExecutor, SandboxUnavailable
from vericode.jobs import run_visible_check
from vericode.sandbox_policy import DEFAULT_IMAGE, ExecutionLimits
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
    sandbox = commands.add_parser("sandbox-info", help="check Linux Docker and the trusted local runner image")
    sandbox.add_argument("--image", default=DEFAULT_IMAGE)
    checks = commands.add_parser("run-tests", help="check repair-visible tests; mock unless --backend docker")
    checks.add_argument("--task", default="clamp")
    checks.add_argument("--data-root", type=Path, default=Path("data"))
    checks.add_argument("--backend", choices=("mock", "docker"), default="mock")
    checks.add_argument("--candidate", choices=("original", "mock"), default="original")
    checks.add_argument("--image", default=DEFAULT_IMAGE)
    checks.add_argument("--timeout", type=float, default=10.0, help="attached execution seconds (0.5-60)")
    checks.add_argument("--output", type=Path, help="new JSON artifact; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        if args.command == "list-tasks":
            manifest = TaskManifest.load(args.data_root / "manifests/development.json")
            for task in manifest.load_tasks(args.data_root / "repair"):
                print(f"{task.task_id}\t{task.split}\t{task.dataset_version}")
        elif args.command == "demo":
            if args.output and args.output.exists():
                raise FileExistsError(f"output already exists: {args.output}")
            record = run_mock_demo(args.data_root, args.task)
            if args.output:
                write_run(args.output, record)
            print(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False))
        elif args.command == "sandbox-info":
            executor = DockerExecutor(args.image)
            print(json.dumps({"available": True, "image": args.image, "image_id": executor.prepare(),
                              "limits": asdict(executor.limits)}, indent=2))
        elif args.command == "run-tests":
            if args.output and args.output.exists():
                raise FileExistsError(f"output already exists: {args.output}")
            record = run_visible_check(
                args.data_root, args.task, backend=args.backend, candidate_origin=args.candidate,
                image=args.image, limits=ExecutionLimits(wall_seconds=args.timeout),
            )
            if args.output:
                write_run(args.output, record)
            print(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False))
            status = record["execution"]["status"]
            if status == "infrastructure_error":
                return 2
            if status not in ("passed", "not_executed"):
                return 1
        else:
            parser.print_help()
    except (ValidationError, SandboxUnavailable, OSError) as exc:
        parser.exit(2, f"vericode: error: {exc}\n")
    return 0
