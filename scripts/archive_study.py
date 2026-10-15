"""Copy completed, validated study evidence into a new reviewable directory."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from vericode.checkpoints import fingerprint, locked_directory
from vericode.records import read_record
from vericode.study import load_study, study_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError(args.output)
    with locked_directory(args.run_dir, resume=True):
        protocol, records = load_study(args.run_dir)
        if fingerprint(protocol) != fingerprint(read_record(args.protocol)):
            raise ValueError("protocol file differs from collected protocol")
        summary = study_summary(protocol, records, 0)
        if summary["pending"]:
            raise ValueError("this archiver requires completed studies; preserve partial source journals separately")
        summary.pop("newly_completed")
        summary["archive_kind"] = "completed pipeline demonstration evidence"
        args.output.mkdir(parents=True)
        for name in ("batch.json", "events.jsonl"):
            shutil.copyfile(args.run_dir / name, args.output / name)
        shutil.copyfile(args.protocol, args.output / "protocol.json")
        (args.output / "collection_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(args.output.iterdir())}
        (args.output / "files.sha256.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "protocol_sha256": protocol["protocol_sha256"], "usage": summary["usage"]}))


if __name__ == "__main__":
    main()
