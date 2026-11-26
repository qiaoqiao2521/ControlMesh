"""T3 Code is the default application; verification stays a separate action."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys

from controlmesh import __version__


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        from controlmesh.t3 import main as launch

        return launch([])
    parser = argparse.ArgumentParser(
        prog="cm",
        description="T3 Code workspace with optional, independent result verification.",
        epilog="No arguments: launch T3 Code. Use 'cm t3 --help' for upstream commands. Legacy tools remain explicit compatibility commands.",
    )
    parser.add_argument("--version", action="version", version=f"ControlMesh {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    commands.add_parser("t3", add_help=False, help="Pass arguments to the locked T3 Code runtime")
    commands.add_parser("verify", add_help=False, help="Check existing results and optional remote delivery")
    commands.add_parser("run", add_help=False, help="Compatibility: execute one external command and verify")
    commands.add_parser("workflow", add_help=False, help="Compatibility: explicit SpecMesh handoff")
    commands.add_parser("closeout", add_help=False, help="Compatibility: explicit Markdown reference sync")
    options, remaining = parser.parse_known_args(arguments)
    if options.command is None:
        if remaining:
            parser.error(f"unrecognized arguments: {' '.join(remaining)}")
        parser.print_help()
        return 0
    if options.command == "t3":
        from controlmesh.t3 import main as run
    elif options.command == "verify":
        from controlmesh.verify import main as run
    elif options.command == "run":
        from controlmesh.execution import main as run
    elif options.command == "workflow":
        from controlmesh.workflow import main as run
    else:
        from controlmesh.closeout import main as run
    return run(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
