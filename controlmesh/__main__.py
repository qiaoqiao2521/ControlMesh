"""Small command dispatcher; importing CM never starts a runtime or a service."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from controlmesh import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cm",
        description="Run an explicit task, verify its artifacts, or prepare a project handoff.",
        epilog="Each command owns its options. Use 'cm run --help' to start.",
    )
    parser.add_argument("--version", action="version", version=f"ControlMesh {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="{run,workflow,closeout}")
    commands.add_parser("run", add_help=False, help="Execute once, verify, and report the next action")
    commands.add_parser("workflow", add_help=False, help="Prepare/check materials with independent SpecMesh")
    commands.add_parser("closeout", add_help=False, help="Explicit, offline Markdown section synchronization")
    options, remaining = parser.parse_known_args(argv)
    if options.command is None:
        if remaining:
            parser.error(f"unrecognized arguments: {' '.join(remaining)}")
        parser.print_help()
        return 0
    if options.command == "run":
        from controlmesh.execution import main as run
    elif options.command == "workflow":
        from controlmesh.workflow import main as run
    else:
        from controlmesh.closeout import main as run
    return run(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
