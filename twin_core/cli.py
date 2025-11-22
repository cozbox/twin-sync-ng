from __future__ import annotations

import argparse

from . import core


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="twin", description="TwinSync++ CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize a twin repository")
    subparsers.add_parser("snapshot", help="Capture live state and logs")
    subparsers.add_parser("plan", help="Calculate drift and actions")
    subparsers.add_parser("apply", help="Apply the latest plan")
    subparsers.add_parser("status", help="Show drift status")
    subparsers.add_parser("logs", help="Show log summary")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        core.init_twin_repo()
    elif args.command == "snapshot":
        core.run_snapshot()
    elif args.command == "plan":
        core.run_plan()
    elif args.command == "apply":
        core.run_apply()
    elif args.command == "status":
        core.run_status()
    elif args.command == "logs":
        core.run_logs()


if __name__ == "__main__":  # pragma: no cover
    main()
