from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import __version__
from .validator import validate_file, validate_run_directory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ccac", description="Validate Cloud & Capital Analysis Contract artifacts")
    parser.add_argument("--version", action="version", version=f"ccac {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate one CCAC JSON artifact")
    validate.add_argument("artifact", type=Path)
    validate.add_argument("--format", choices=("text", "json"), default="text")

    validate_run = subparsers.add_parser("validate-run", help="Validate a CCAC run directory")
    validate_run.add_argument("run_directory", type=Path)
    validate_run.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _render(issues, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps({"valid": not issues, "issues": [issue.as_dict() for issue in issues]}, indent=2))
        return
    if not issues:
        print("CCAC validation passed.")
        return
    print(f"CCAC validation failed with {len(issues)} issue(s):")
    for issue in issues:
        print(f"- {issue.code.value} at {issue.path}: {issue.message}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        issues = validate_file(args.artifact)
    else:
        issues = validate_run_directory(args.run_directory)
    _render(issues, args.format)
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
