"""Run one explicit local command, check its result, and report the next action.

This is a synchronous Linux CLI, not an agent, sandbox, scheduler, or retry loop.
Task text is never interpreted as commands. The caller supplies every command and
keeps responsibility for permissions and for choosing meaningful verification.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any


_SCHEMA = "controlmesh.execution.v1"
_MAX_PREVIOUS = 2 * 1024 * 1024


def _seconds(value: str) -> float:
    result = float(value)
    if not math.isfinite(result) or not 0 < result <= 86400:
        raise argparse.ArgumentTypeError("timeout must be positive and at most 86400 seconds")
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cm run", description="Execute once, verify actual results, and write a private local report (Linux)."
    )
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--task", help="Optional existing task file inside cwd; recorded, never executed")
    parser.add_argument("--report", type=Path, required=True, help="New JSON file; relative paths use cwd")
    parser.add_argument("--verify", action="append", default=[], help="Explicit verification argv, parsed without a shell; repeatable")
    parser.add_argument("--artifact", action="append", default=[], help="Required regular file inside cwd; repeatable, not a write boundary")
    parser.add_argument("--timeout", type=_seconds, default=900.0, help="Total seconds for execution and verification (default: 900)")
    parser.add_argument("--previous-report", type=Path, help="Prior report of the same task and verification contract")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- COMMAND ARG ...")
    return parser


def _at(root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return Path(os.path.abspath(path if path.is_absolute() else root / path))


def _project_file(root: Path, value: str | Path, *, required: bool = False) -> Path:
    path = _at(root, value)
    try:
        parts = path.relative_to(root).parts
    except ValueError as exc:
        raise ValueError("task and artifact paths must remain inside cwd") from exc
    current = root
    for part in parts:
        current /= part
        if current.is_symlink():
            raise ValueError("task and artifact paths must not contain symlinks")
    if path.exists() and not path.is_file():
        raise ValueError("task and artifacts must be regular files")
    if required and not path.is_file():
        raise ValueError("task file does not exist")
    return path


def _digest_file(path: Path) -> tuple[str, int]:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("expected a regular file")
        digest = hashlib.sha256()
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
        return digest.hexdigest(), info.st_size


def _artifact(root: Path, path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path.relative_to(root)), "exists": False}
    try:
        _project_file(root, path)
        digest, size = _digest_file(path)
        result.update(exists=True, sha256=digest, size_bytes=size)
    except FileNotFoundError:
        result["error"] = "missing"
    except (OSError, ValueError):
        result["error"] = "not_a_readable_regular_file"
    return result


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _read_previous(path: Path, identity: dict[str, Any]) -> dict[str, Any]:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("previous report must be a regular file")
        raw = source.read(_MAX_PREVIOUS + 1)
    if len(raw) > _MAX_PREVIOUS:
        raise ValueError("previous report is too large")
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != _SCHEMA
        or value.get("identity") != identity
        or not isinstance(value.get("evidence"), dict)
        or value.get("evidence_fingerprint") != _fingerprint(value["evidence"])
    ):
        raise ValueError("previous report does not match this cwd, task, or verification contract")
    return value


def _process_identity(pid: int) -> tuple[int, int, str] | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return int(fields[1]), int(fields[19]), fields[0]
    except (OSError, ValueError, IndexError):
        return None


def _collect_owned(owned: dict[int, int]) -> None:
    """Collect this dedicated supervisor's children, including adopted orphans."""
    snapshot = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdecimal() and (identity := _process_identity(int(entry.name))):
            snapshot[int(entry.name)] = identity
    for pid, (parent, born, _) in snapshot.items():
        if parent == os.getpid() and pid not in owned:
            owned[pid] = born
    parents = {pid for pid, born in owned.items() if pid in snapshot and snapshot[pid][1] == born}
    while parents:
        children = {pid for pid, (parent, _, _) in snapshot.items() if parent in parents and pid not in owned}
        for pid in children:
            owned[pid] = snapshot[pid][1]
        parents = children


def _cleanup(proc: subprocess.Popen, owned: dict[int, int]) -> bool:
    """Stop only this invocation's descendants; never kill a shared process group."""
    for sig, grace in ((signal.SIGTERM, 0.15), (signal.SIGKILL, 1.0)):
        deadline = time.monotonic() + grace
        while True:
            _collect_owned(owned)
            alive = []
            for pid, born in reversed(tuple(owned.items())):
                current = _process_identity(pid)
                if current and current[1] == born and current[2] != "Z":
                    alive.append(pid)
                    with contextlib.suppress(OSError):
                        os.kill(pid, sig)
            if not alive:
                # Preserve the command's return code before reaping adoptees.
                proc.wait(timeout=1)
                while True:
                    try:
                        reaped, _ = os.waitpid(-1, os.WNOHANG)
                    except ChildProcessError:
                        return True  # ECHILD, not a potentially stale snapshot.
                    if reaped == 0:
                        # A TERM handler may have forked after our snapshot.
                        # Rescan and stop its adopted child within this budget.
                        break
            if time.monotonic() >= deadline:
                break
            time.sleep(0.02)
    return False


@contextlib.contextmanager
def _signals(abort: list[int]):
    previous = {}
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous[sig] = signal.getsignal(sig)
            signal.signal(sig, lambda signum, _frame: abort.__setitem__(0, signum))
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def _run_owned(argv: list[str], cwd: Path, logs: Path, label: str, deadline: float, abort: list[int]) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {"argv": argv, "state": "not_started", "exit_code": None}
    owned: dict[int, int] = {}
    proc = None
    with contextlib.ExitStack() as stack:
        output = []
        for stream in ("stdout", "stderr"):
            path = logs / f"{label}.{stream}.log"
            handle = stack.enter_context(os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"))
            output.append(handle)
            result[f"{stream}_log"] = f"{logs.name}/{path.name}"
        try:
            if abort[0]:
                result["state"] = "interrupted"
            elif time.monotonic() >= deadline:
                result["state"] = "timed_out"
            else:
                proc = subprocess.Popen(
                    argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=output[0], stderr=output[1],
                    shell=False, start_new_session=True,
                )
                current = _process_identity(proc.pid)
                if current:
                    owned[proc.pid] = current[1]
                while True:
                    _collect_owned(owned)
                    if abort[0]:
                        result["state"] = "interrupted"
                        break
                    if proc.poll() is not None:
                        result.update(state="succeeded" if proc.returncode == 0 else "failed", exit_code=proc.returncode)
                        break
                    if time.monotonic() >= deadline:
                        result["state"] = "timed_out"
                        break
                    time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        except OSError as exc:
            result.update(state="unavailable", error=type(exc).__name__, errno=exc.errno)
        finally:
            if proc is not None:
                result["cleanup_complete"] = _cleanup(proc, owned)
                result["exit_code"] = proc.returncode
    result["duration_seconds"] = round(time.monotonic() - started, 3)
    return result


def _run(argv: list[str], cwd: Path, logs: Path, label: str, deadline: float, abort: list[int]) -> dict[str, Any]:
    # One short-lived supervisor owns exactly one command tree. It has no
    # pre-existing children, so even double-forked children with env={} remain
    # attributable after reparenting. The host's children are never adopted.
    parent = os.getpid()
    failed = {"argv": argv, "state": "failed", "exit_code": None,
              "cleanup_complete": False, "error": "supervisor_failed"}
    with tempfile.TemporaryFile(dir=logs) as receipt:
        supervisor = os.fork()
        if supervisor == 0:
            code = 0
            try:
                libc = ctypes.CDLL(None, use_errno=True)
                if libc.prctl(36, 1, 0, 0, 0) or libc.prctl(1, signal.SIGTERM, 0, 0, 0):
                    raise OSError("dedicated child cleanup is unavailable")
                if os.getppid() != parent:
                    abort[0] = signal.SIGTERM
                result = _run_owned(argv, cwd, logs, label, deadline, abort)
            except BaseException:
                result, code = failed, 1
            try:
                receipt.write(json.dumps(result, allow_nan=False).encode())
                receipt.flush()
            except BaseException:
                code = 1
            os._exit(code)
        requested_at = None
        deadline_stop = False
        while True:
            ended, wait_status = os.waitpid(supervisor, os.WNOHANG)
            if ended:
                if os.waitstatus_to_exitcode(wait_status) != 0:
                    return failed
                break
            now = time.monotonic()
            if requested_at is None and (abort[0] or now >= deadline):
                requested_at = now
                deadline_stop = not abort[0]
                with contextlib.suppress(ProcessLookupError):
                    os.kill(supervisor, abort[0] or signal.SIGTERM)
            if requested_at is not None and now - requested_at > 3:
                # A crashed/hung supervisor is an uncertain cleanup, never a
                # successful run. Do not conceal it behind a completed receipt.
                with contextlib.suppress(ProcessLookupError):
                    os.kill(supervisor, signal.SIGKILL)
                os.waitpid(supervisor, 0)
                return failed
            time.sleep(0.02)
        receipt.seek(0)
        try:
            result = json.loads(receipt.read(_MAX_PREVIOUS + 1))
            if not isinstance(result, dict) or "state" not in result or "exit_code" not in result:
                return failed
            if deadline_stop and result["state"] == "interrupted":
                result["state"] = "timed_out"
            return result
        except (ValueError, UnicodeError):
            return failed


def _outcome(execution: dict, checks: list[dict], artifacts: list[dict], abort: int) -> tuple[str, str, str, int]:
    stages = [execution, *checks]
    if abort:
        return "interrupted", "review_interruption", "Execution was interrupted; inspect the report before continuing.", 128 + abort
    if any(stage.get("cleanup_complete") is False for stage in stages):
        return "needs_repair", "diagnose_cleanup", "An owned child could not be confirmed stopped; inspect before any new attempt.", 1
    if any(stage["state"] == "timed_out" for stage in stages):
        return "timed_out", "diagnose_timeout", "The total time budget expired; inspect the failing stage before deciding how to continue.", 124
    if execution["state"] == "unavailable":
        return "tool_unavailable", "use_host_agent", "The command could not start; the host agent can continue the task using its available tools.", 4
    if execution["state"] != "succeeded" or any(stage["state"] == "failed" for stage in checks) or any(not item["exists"] for item in artifacts):
        return "needs_repair", "repair", "Execution, a declared verification, or a required artifact did not pass.", 1
    if not checks or any(stage["state"] != "succeeded" for stage in checks):
        return "unverified", "verify", "No complete successful verification is available; inspect the actual result before delivery.", 3
    return "completed", "deliver", "The explicit command, declared verification, and required artifacts passed; deliver within existing authorization.", 0


def _publish(path: Path, report: dict[str, Any]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            json.dump(report, target, ensure_ascii=False, indent=2, allow_nan=False)
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        # Atomic and no-clobber: another process cannot turn this into an
        # overwrite of an input, artifact, or report that appeared meanwhile.
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    options = parser.parse_args(argv)
    try:
        if not sys.platform.startswith("linux"):
            raise ValueError("cm run currently requires Linux for owned child process cleanup")
        cwd = options.cwd.expanduser().resolve(strict=True)
        if not cwd.is_dir():
            raise ValueError("cwd must be an existing directory")
        command = options.command[1:] if options.command[:1] == ["--"] else options.command
        if not command or any("\0" in part for part in command):
            raise ValueError("supply an explicit command after --")
        verification = [shlex.split(value) for value in options.verify]
        if any(not item or any("\0" in part for part in item) for item in verification):
            raise ValueError("verification commands must not be empty")
        task = _project_file(cwd, options.task, required=True) if options.task else None
        artifacts = list(dict.fromkeys(_project_file(cwd, item) for item in options.artifact))
        report_path = _at(cwd, options.report)
        report_path = report_path.parent.resolve(strict=True) / report_path.name
        logs = report_path.with_name(report_path.name + ".logs")
        if os.path.lexists(report_path) or os.path.lexists(logs):
            raise ValueError("report and log paths must be new; existing files are never overwritten")
        if any(path == report_path or path == logs or logs in path.parents for path in [*artifacts, *([task] if task else [])]):
            raise ValueError("report/log paths overlap a task or artifact")
        identity: dict[str, Any] = {
            "cwd": str(cwd),
            "task": {"path": str(task.relative_to(cwd)), "sha256": _digest_file(task)[0]} if task else None,
            "verification": verification,
            "artifacts": [str(path.relative_to(cwd)) for path in artifacts],
        }
        if task is None:
            identity["command"] = command
        previous = _read_previous(_at(cwd, options.previous_report), identity) if options.previous_report else None
        logs.mkdir(mode=0o700)
        started_at = datetime.now(UTC).isoformat()
        abort = [0]
        with _signals(abort):
            deadline = time.monotonic() + options.timeout
            execution = _run(command, cwd, logs, "execution", deadline, abort)
            checks = []
            if execution["state"] in {"succeeded", "failed"} and execution.get("cleanup_complete"):
                for index, check in enumerate(verification):
                    stage = _run(check, cwd, logs, f"verify-{index + 1}", deadline, abort)
                    checks.append(stage)
                    if stage["state"] in {"interrupted", "timed_out"} or not stage.get("cleanup_complete", True):
                        break
            observed = [_artifact(cwd, path) for path in artifacts]
            status, action, reason, code = _outcome(execution, checks, observed, abort[0])
            evidence = {
                "execution_state": execution["state"], "execution_exit_code": execution["exit_code"],
                "verification": [{"argv": check["argv"], "state": check["state"], "exit_code": check["exit_code"]} for check in checks],
                "artifacts": observed,
            }
            fingerprint = _fingerprint(evidence)
            comparison = None
            if previous:
                changed = previous["evidence_fingerprint"] != fingerprint
                comparison = {"evidence_changed": changed, "advisory": True}
                if not changed and action in {"repair", "verify"}:
                    action = "change_approach"
                    reason = "The recorded execution/verification outcomes and artifact summary are unchanged; inspect logs and choose a different approach instead of repeating automatically."
            report = {
                "schema_version": _SCHEMA, "identity": identity,
                "started_at": started_at, "finished_at": datetime.now(UTC).isoformat(),
                "status": status, "next_action": action, "next_action_reason": reason, "advisory": True,
                "execution": execution, "verification": checks, "artifacts": observed,
                "comparison": comparison, "evidence": evidence, "evidence_fingerprint": fingerprint,
                "logs_directory": logs.name,
            }
            _publish(report_path, report)
        print(json.dumps({"status": status, "next_action": action, "report": str(report_path), "advisory": True}))
        return code
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"error": "invalid_execution_request", "detail": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
