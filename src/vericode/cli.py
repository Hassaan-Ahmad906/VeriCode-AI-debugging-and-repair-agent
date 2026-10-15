"""Local CLI: mock by default, explicit Docker execution for visible checks."""

import argparse
from dataclasses import asdict
from collections.abc import Sequence
import json
from pathlib import Path

from vericode import __version__
from vericode.datasets import TaskManifest, read_json
from vericode.batch import run_batch
from vericode.experiments import run_mock_demo, write_run
from vericode.docker_executor import DockerExecutor, SandboxUnavailable
from vericode.jobs import run_visible_check
from vericode.direct_run import run_direct
from vericode.feedback_run import run_feedback
from vericode.augmented import run_augmented
from vericode.feedback import FeedbackLimits
from vericode.model_io import GenerationLimits
from vericode.run_config import AugmentedConfiguration, FeedbackConfiguration, RunConfiguration
from vericode.sandbox_policy import DEFAULT_IMAGE, ExecutionLimits
from vericode.schemas import ValidationError
from vericode.scoring import score_record
from vericode.records import read_record
from vericode.protocol import freeze_protocol
from vericode.study import run_study


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
    repair = commands.add_parser("repair", help="strategy A: one mock response, then optional Docker visible checks")
    feedback = commands.add_parser("feedback", help="strategy B: bounded visible-feedback repair; mock by default")
    augment = commands.add_parser("augment", help="strategy C: independently validated generated cases plus feedback")
    for command in (repair, feedback, augment):
        command.add_argument("--task", default="clamp")
        command.add_argument("--data-root", type=Path, default=Path("data"))
        command.add_argument("--provider", choices=("mock",), default="mock")
        command.add_argument("--model", default="scripted-v1", help="configured model identifier; mock uses scripted responses")
        command.add_argument("--backend", choices=("mock", "docker"), default="mock")
        command.add_argument("--image", default=DEFAULT_IMAGE)
        command.add_argument("--timeout", type=float, default=10.0)
        command.add_argument("--max-output-tokens", type=int, default=2048)
        command.add_argument("--output", type=Path, help="new JSON artifact; existing files are never overwritten")
    repair.add_argument("--max-model-calls", type=int, default=3, help="transport call limit; one repair response")
    for command in (feedback, augment):
        command.add_argument("--max-model-calls", type=int, default=6, help="shared transport-call ceiling, including generation for C (1-30)")
        command.add_argument("--max-attempts", type=int, default=3, help="repair attempts (1-10), separate from transport retries")
        command.add_argument("--max-transport-calls", type=int, default=3, help="transport calls per response (1-3)")
        command.add_argument("--feedback-bytes", type=int, default=8192, help="visible output bytes per request (256-16384)")
    batch = commands.add_parser("batch", help="run a fixed repair batch and resume recorded outcomes")
    batch.add_argument("--config", type=Path, default=Path("configs/offline_direct.json"))
    batch.add_argument("--manifest", type=Path, default=Path("data/manifests/development.json"))
    batch.add_argument("--data-root", type=Path, default=Path("data"))
    batch.add_argument("--run-dir", type=Path, required=True)
    batch.add_argument("--resume", action="store_true", help="skip completed outcomes; never replay uncertain started tasks")
    evaluate = commands.add_parser("evaluate", help="independently score a saved repair; never sends feedback to models")
    evaluate.add_argument("--record", type=Path, required=True)
    evaluate.add_argument("--data-root", type=Path, default=Path("data"))
    evaluate.add_argument("--backend", choices=("mock", "docker"), default="mock")
    evaluate.add_argument("--image", default=DEFAULT_IMAGE)
    evaluate.add_argument("--timeout", type=float, default=10.0)
    evaluate.add_argument("--output", type=Path)
    study = commands.add_parser("study", help="freeze and collect offline A/B/C pipeline demonstrations")
    study_commands = study.add_subparsers(dest="study_command", required=True)
    freeze = study_commands.add_parser("freeze", help="record fixed data/code/configuration before collection")
    freeze.add_argument("--config", type=Path, default=Path("configs/study_mock.json"))
    freeze.add_argument("--data-root", type=Path, default=Path("data"))
    freeze.add_argument("--split", choices=("development", "final"), default="development")
    freeze.add_argument("--output", type=Path, required=True)
    collect = study_commands.add_parser("run", help="finish all repairs, then independent scoring; durable resumption")
    collect.add_argument("--protocol", type=Path, required=True)
    collect.add_argument("--data-root", type=Path, default=Path("data"))
    collect.add_argument("--run-dir", type=Path, required=True)
    collect.add_argument("--resume", action="store_true")
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
        elif args.command in ("repair", "feedback", "augment"):
            if args.output and (args.output.exists() or args.output.is_symlink()):
                raise FileExistsError(f"output already exists: {args.output}")
            generation = GenerationLimits(output_tokens=args.max_output_tokens,
                                          max_transport_calls=args.max_model_calls if args.command == "repair" else args.max_transport_calls)
            execution = ExecutionLimits(wall_seconds=args.timeout)
            if args.command in ("feedback", "augment"):
                config_class = FeedbackConfiguration if args.command == "feedback" else AugmentedConfiguration
                config = config_class(args.provider, args.model, args.backend, args.image, generation, execution,
                                               FeedbackLimits(args.max_attempts, args.max_model_calls, args.feedback_bytes))
                controller = run_feedback if args.command == "feedback" else run_augmented
                record = controller(args.data_root, args.task, config)
            else:
                config = RunConfiguration(args.provider, args.model, args.backend, args.image, generation, execution)
                record = run_direct(args.data_root, args.task, config)
            if args.output:
                write_run(args.output, record)
            print(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False))
            if record["status"] in ("infrastructure_error", "provider_error", "transport_error", "transient_error", "paid_execution_disabled"):
                return 2
            return 0 if record["status"] in ("candidate_ready", "visible_passed") else 1
        elif args.command == "study":
            if args.study_command == "freeze":
                if args.output.exists() or args.output.is_symlink():
                    raise FileExistsError(f"output already exists: {args.output}")
                record = freeze_protocol(args.data_root, read_json(args.config), args.split)
                write_run(args.output, record)
                print(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False))
            else:
                record = run_study(args.data_root, read_record(args.protocol), args.run_dir, resume=args.resume)
                print(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False))
                if record["pending"] or record["evaluation"]["infrastructure_errors"]:
                    return 2
        elif args.command == "evaluate":
            if args.output and (args.output.exists() or args.output.is_symlink()):
                raise FileExistsError(f"output already exists: {args.output}")
            config = RunConfiguration(backend=args.backend, image=args.image, execution=ExecutionLimits(wall_seconds=args.timeout))
            record = score_record(args.data_root, read_record(args.record), config)
            if args.output:
                write_run(args.output, record)
            print(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False))
            if record["status"] == "infrastructure_error":
                return 2
            return 0 if record["suite_passed"] is True or args.backend == "mock" else 1
        elif args.command == "batch":
            config = RunConfiguration.from_dict(read_json(args.config))
            result = run_batch(args.data_root, args.manifest, config, args.run_dir, resume=args.resume)
            print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
            if result["pending"] or result["outcomes"].get("infrastructure_error"):
                return 2
            return 0 if all(status in ("candidate_ready", "visible_passed") for status in result["outcomes"]) else 1
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
