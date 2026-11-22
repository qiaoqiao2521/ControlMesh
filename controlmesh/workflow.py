"""Explicit, file-based handoff through a trusted independent SpecMesh checkout.

SpecMesh owns extraction, its schemas, and pre-consumption verification. This
adapter selects that interface and preserves its JSON. ``executable`` means the
selected material can be consumed; it is neither business acceptance nor a grant
to execute commands. No task runner, provider, runtime state, or file writer is
started here.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


_HANDOFF_VERSION = "specmesh.handoff.v1"
_MAX_OUTPUT = 1024 * 1024


def _relative_path(value: str) -> str:
    if (
        not value
        or Path(value).is_absolute()
        or "\\" in value
        or any(ord(char) < 32 for char in value)
        or any(part in {"", ".", "..", ".git"} for part in value.split("/"))
    ):
        raise argparse.ArgumentTypeError("use a literal repository-relative path")
    return value


def _timeout(value: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be positive and at most 60 seconds") from exc
    if not math.isfinite(result) or not 0 < result <= 60:
        raise argparse.ArgumentTypeError("timeout must be positive and at most 60 seconds")
    return result


def _head(value: str) -> str:
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
        raise argparse.ArgumentTypeError("expected-head must be a full lowercase Git object ID")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cm-workflow",
        description=(
            "Prepare or check ordinary handoff files through an explicitly trusted SpecMesh checkout. "
            "executable means consumable material, not business acceptance or execution authorization."
        ),
    )
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("prepare", "check"):
        command = commands.add_parser(name)
        command.add_argument("--repo", type=Path, required=True, help="Explicit project repository root")
        command.add_argument("--task", type=_relative_path, required=True, help="Selected relative plan directory")
        command.add_argument("--scope", action="append", type=_relative_path, default=[], help="Explicit relative file; repeat as needed")
        command.add_argument("--specmesh-root", type=Path, required=True, help="Trusted independent SpecMesh code checkout")
        command.add_argument("--timeout", type=_timeout, default=5.0)
        if name == "prepare":
            command.add_argument("--expected-head", type=_head, required=True)
        else:
            command.add_argument("--handoff", required=True, help="Handoff file relative to this command's cwd, or - for stdin")
    return parser


def _reject_constant(_value: str) -> None:
    raise ValueError("invalid_specmesh_json")


def _response(raw: bytes, options: argparse.Namespace) -> dict[str, Any]:
    """Recognize the selected interface, without duplicating its upstream schema."""
    if not raw or len(raw) > _MAX_OUTPUT:
        raise ValueError("missing_or_oversized_specmesh_response")
    value = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != _HANDOFF_VERSION
        or type(value.get("executable")) is not bool
        or not isinstance(value.get("state"), str)
        or not isinstance(value.get("issues"), list)
    ):
        raise ValueError("expected_specmesh_handoff_interface")
    if options.operation == "prepare":
        if not isinstance(value.get("baseline"), dict) or not isinstance(value.get("task"), dict):
            raise ValueError("expected_prepared_handoff")
        if value["executable"] and (
            value["baseline"].get("observed_head") != options.expected_head
            or value["baseline"].get("expected_head") != options.expected_head
            or value["task"].get("path") != options.task
        ):
            raise ValueError("specmesh_selection_mismatch")
    elif type(value.get("verified")) is not bool or value["verified"] != value["executable"]:
        raise ValueError("expected_handoff_verification")
    if value["executable"] and (
        value["state"] != "ready"
        or any(isinstance(issue, dict) and issue.get("severity") == "error" for issue in value["issues"])
    ):
        raise ValueError("inconsistent_specmesh_response")
    return value


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    try:
        repo = options.repo.expanduser().resolve(strict=True)
        specmesh = options.specmesh_root.expanduser().resolve(strict=True)
        if not repo.is_dir() or not (specmesh / "specmesh_port/__main__.py").is_file():
            raise ValueError("project_or_independent_specmesh_unavailable")
        command = [sys.executable, "-B", "-S", "-E", "-X", "utf8", "-m", "specmesh_port",
                   "--allowed-root", str(repo)]
        if options.operation == "prepare":
            command += ["--handoff", "json"]
            request = {
                "contract_version": "specmesh.port.v1-draft",
                "operation": "prepare_handoff",
                "repo_root": str(repo),
                "expected_head": options.expected_head,
                "task_path": options.task,
                "mode": "read_only",
            }
            incoming = json.dumps(request, ensure_ascii=False).encode("utf-8")
        else:
            # Preserve a final symlink so the upstream O_NOFOLLOW check can reject
            # it. Resolving this path would silently defeat that check.
            path = Path(options.handoff).expanduser()
            handoff = "-" if options.handoff == "-" else str(path if path.is_absolute() else Path.cwd() / path)
            command += ["--verify-handoff", handoff, "--task-path", options.task]
            incoming = sys.stdin.buffer.read(_MAX_OUTPUT + 1) if handoff == "-" else b""
            if len(incoming) > _MAX_OUTPUT:
                raise ValueError("handoff_input_too_large")
        for path in options.scope:
            command += ["--scope-path", path]
        # No provider credentials, Python import overrides, or user runtime
        # configuration are passed. SpecMesh retains its own read-only Git rules.
        environment = {"PATH": os.environ.get("PATH", "")}
        if "SYSTEMROOT" in os.environ:
            environment["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
        result = subprocess.run(command, cwd=specmesh, env=environment, input=incoming,
                                capture_output=True, timeout=options.timeout, check=False)
        if len(result.stderr) > 65536:
            raise ValueError("specmesh_error_output_limit")
        sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
        value = _response(result.stdout, options)
        binary_stdout = getattr(sys.stdout, "buffer", None)
        if binary_stdout is None:
            sys.stdout.write(result.stdout.decode("utf-8"))
        else:
            binary_stdout.write(result.stdout)
        if result.returncode:
            return result.returncode if result.returncode > 0 else 1
        return 0 if value["executable"] else 3
    except subprocess.TimeoutExpired:
        print(json.dumps({"error": "specmesh_timeout"}), file=sys.stderr)
    except (OSError, ValueError, UnicodeError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]+", str(exc)) else type(exc).__name__
        print(json.dumps({"error": "workflow_request_failed", "detail": detail}), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
