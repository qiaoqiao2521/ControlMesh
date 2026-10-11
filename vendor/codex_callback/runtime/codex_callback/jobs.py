"""Public functions for detached jobs and callbacks; no command-line parser."""

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from .client import CodexClient

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = Path(
    os.environ.get(
        "CODEX_CALLBACK_RUNS",
        str(
            Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
            / "codex-callback/runs"
        ),
    )
).expanduser()


def save_status(state):
    """Atomically publish a complete state file; each run has one worker writer."""
    path = Path(state["directory"]) / "status.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def read_status(directory):
    """Read process outcome and callback receipt without contacting Codex."""
    return json.loads((Path(directory) / "status.json").read_text())


def _create_state(
    thread_id,
    cwd,
    followup,
    runs_dir,
    socket_path,
    callback_wait_seconds,
    *,
    preflight=True,
):
    thread_id = str(uuid.UUID(thread_id or os.environ["CODEX_THREAD_ID"]))
    cwd = Path(cwd).expanduser().resolve(strict=True)
    if not cwd.is_dir() or not followup.strip():
        raise ValueError("cwd must be a directory and followup must be nonempty")
    if callback_wait_seconds <= 0:
        raise ValueError("callback_wait_seconds must be positive")
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    socket_path = (
        Path(socket_path or codex_home / "app-server-control/app-server-control.sock")
        .expanduser()
        .resolve()
    )
    # Validate the destination before starting potentially expensive work.
    if preflight:
        with CodexClient(socket_path) as client:
            thread = client.read_thread(thread_id)
            if thread.get("canAcceptDirectInput") is False:
                raise ValueError("The target task does not accept direct input")
    runs = Path(runs_dir).expanduser().resolve()
    runs.mkdir(mode=0o700, parents=True, exist_ok=True)
    event_id = str(uuid.uuid4())
    directory = runs / event_id
    directory.mkdir(mode=0o700)
    return {
        "version": 1,
        "id": event_id,
        "thread_id": thread_id,
        "socket_path": str(socket_path),
        "directory": str(directory),
        "cwd": str(cwd),
        "created_at": time.time(),
        "followup": followup,
        "callback_wait_seconds": callback_wait_seconds,
        "callback": {"status": "pending"},
    }


def _spawn(directory):
    env = dict(os.environ)
    env["CODEX_CALLBACK_DIRECTORY"] = str(directory)
    with (Path(directory) / "worker.log").open("ab") as output:
        proc = subprocess.Popen(
            [sys.executable, "-m", "codex_callback.worker"],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            umask=0o077,
        )
    return proc.pid


def start_job(
    command,
    *,
    cwd,
    followup,
    thread_id=None,
    runs_dir=DEFAULT_RUNS,
    socket_path=None,
    timeout_seconds=None,
    callback_wait_seconds=86400,
):
    """Launch a detached supervisor and return its private run directory.

    Pass the exact executable and argument list; no shell expansion is performed.
    From a Codex shell, the original task ID comes from CODEX_THREAD_ID.
    """
    if (
        isinstance(command, (str, bytes))
        or not command
        or not all(isinstance(part, str) and part for part in command)
    ):
        raise ValueError("command must be a nonempty sequence of nonempty strings")
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    state = _create_state(
        thread_id, cwd, followup, runs_dir, socket_path, callback_wait_seconds
    )
    state.update(
        command=list(command), timeout_seconds=timeout_seconds, outcome="pending"
    )
    save_status(state)
    _spawn(state["directory"])
    return Path(state["directory"])


def notify(
    *,
    followup,
    cwd,
    outcome="completed",
    thread_id=None,
    runs_dir=DEFAULT_RUNS,
    socket_path=None,
    callback_wait_seconds=86400,
):
    """Send an event from an existing workflow without launching another job."""
    if outcome not in {"completed", "failed", "cancelled", "timed_out"}:
        raise ValueError("Unsupported event outcome")
    state = _create_state(
        thread_id,
        cwd,
        followup,
        runs_dir,
        socket_path,
        callback_wait_seconds,
        preflight=False,
    )
    state.update(command=None, outcome=outcome, finished_at=time.time())
    (Path(state["directory"]) / "job.log").write_text(
        "External workflow notification.\n"
    )
    save_status(state)
    _spawn(state["directory"])
    return Path(state["directory"])


def retry_callback(directory):
    """Reconcile and retry an existing callback, never rerun its training command."""
    directory = Path(directory).expanduser().resolve(strict=True)
    state = read_status(directory)
    if state["outcome"] in {"pending", "running"}:
        raise ValueError("The job has not recorded a terminal outcome")
    if state["callback"]["status"] == "started":
        return directory
    _spawn(directory)
    return directory
