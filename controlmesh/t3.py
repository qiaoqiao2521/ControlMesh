"""Pass commands to T3 Code; T3 owns threads, providers and execution state.

The checkout's npm lock selects the upstream runtime. An installed Python wheel
can name that runtime explicitly with CONTROL_MESH_T3_BINARY. This module does
not discover credentials, start another agent loop, or interpret a successful
CLI exit as task acceptance.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from collections.abc import Sequence


class T3BinaryNotFound(FileNotFoundError):
    """The selected T3 runtime has not been installed at its explicit path."""


def resolve_t3_binary(
    override: str | Path | None = None,
    *,
    repository_root: Path | None = None,
) -> Path:
    """Resolve an explicit executable or this checkout's pinned npm executable.

    No PATH fallback: a globally installed release must not silently replace
    the runtime selected by this checkout's lockfile.
    """
    selected = override if override is not None else os.environ.get("CONTROL_MESH_T3_BINARY")
    root = repository_root if repository_root is not None else Path(__file__).resolve().parent.parent
    candidate = Path(selected).expanduser() if selected else root / "node_modules" / ".bin" / "t3"
    candidate = candidate.absolute()
    if not candidate.is_file():
        raise T3BinaryNotFound(
            f"T3 Code executable not found: {candidate}. "
            "Run npm ci in the ControlMesh checkout, or set CONTROL_MESH_T3_BINARY "
            "to an installed T3 Code executable."
        )
    if not os.access(candidate, os.X_OK):
        raise PermissionError(f"T3 Code executable is not executable: {candidate}")
    return candidate


def run_t3(
    arguments: Sequence[str],
    *,
    binary: str | Path | None = None,
    repository_root: Path | None = None,
    cwd: str | Path | None = None,
    input_text: str | None = None,
    capture_output: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke T3 once with unchanged arguments, streams and return code.

    Streams are inherited unless capture_output is requested. With a captured
    ``thread start/send --wait --json``, callers may read T3's own JSON status;
    exit 2 alone cannot distinguish waiting for input from a CLI usage error.

    A timeout or interrupted wait only stops this CLI process. It does not
    cancel a thread already running on the T3 server. No retry is attempted.
    """
    executable = resolve_t3_binary(binary, repository_root=repository_root)
    return subprocess.run(
        [str(executable), *arguments],
        cwd=cwd,
        input=input_text,
        capture_output=capture_output,
        text=True,
        shell=False,
        check=False,
        timeout=timeout,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Replace this CLI with T3 so streams, exit status and signals stay native."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        executable = resolve_t3_binary()
        os.execv(str(executable), [str(executable), *arguments])
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 127
    except OSError as exc:
        print(f"Could not launch T3 Code: {exc}", file=sys.stderr)
        return 126
    except KeyboardInterrupt:
        # Only reachable before exec; once replaced, T3 handles its own signals.
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
