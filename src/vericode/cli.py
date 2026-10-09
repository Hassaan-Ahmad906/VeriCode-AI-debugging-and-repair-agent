"""Command-line entry point. All Day 1 operations are offline."""

import argparse
from collections.abc import Sequence

from vericode import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vericode",
        description="Local Python repair research; mock/offline operation by default.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    parser.print_help()
    return 0
