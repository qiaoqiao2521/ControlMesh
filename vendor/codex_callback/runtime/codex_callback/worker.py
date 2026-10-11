"""Detached supervisor: wait for the process, persist outcome, deliver callback."""

import fcntl
import logging
import os
import signal
import subprocess
import time
from pathlib import Path

from .delivery import deliver
from .jobs import read_status, save_status

logger = logging.getLogger(__name__)


class JobCancelled(Exception):
    """Interrupt the supervisor's wait so it can stop its own process group."""


def stop_process(process):
    """Stop only this run's process group, escalating after five seconds."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return process.wait()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    # The leader may exit while a child ignores SIGTERM. Clean up the whole group.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return process.wait()


def run_process(state):
    """Capture the real exit code, including signals and a configured timeout."""
    state.update(outcome="running", started_at=time.time())
    save_status(state)
    process = None

    def cancel(signum, frame):
        raise JobCancelled

    previous = {
        sig: signal.signal(sig, cancel) for sig in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        with (Path(state["directory"]) / "job.log").open("ab") as output:
            process = subprocess.Popen(
                state["command"],
                cwd=state["cwd"],
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                umask=0o077,
            )
            state["process_pid"] = process.pid
            save_status(state)
            try:
                returncode = process.wait(timeout=state["timeout_seconds"])
                outcome = "completed" if returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                returncode = stop_process(process)
                outcome = "timed_out"
            state.update(outcome=outcome, returncode=returncode)
    except JobCancelled:
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        returncode = stop_process(process) if process is not None else None
        state.update(outcome="cancelled", returncode=returncode)
    except OSError as error:
        state.update(outcome="failed", returncode=None, process_error=str(error))
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    state["finished_at"] = time.time()
    save_status(state)


def deliver_with_retries(state):
    """Retry transport outages locally; reconcile before every new send."""
    deadline = time.monotonic() + state["callback_wait_seconds"]
    delay = 2
    while True:
        try:
            deliver(state, save_status, deadline=deadline)
            return
        except OSError as error:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            state["callback"]["error"] = f"{type(error).__name__}: {error}"
            state["callback"]["error_at"] = time.time()
            save_status(state)
            logger.warning("Codex connection unavailable; retrying locally: %s", error)
            time.sleep(min(delay, remaining))
            delay = min(60, delay * 2)


def work(directory):
    """Own one run under an OS lock, preserving failures for explicit recovery."""
    directory = Path(directory)
    with (directory / "worker.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        state = read_status(directory)
        state["worker_pid"] = os.getpid()
        save_status(state)
        if state["outcome"] == "pending":
            run_process(state)
        elif state["outcome"] == "running":
            raise RuntimeError(
                "Previous supervisor exited before recording the job outcome"
            )
        try:
            deliver_with_retries(state)
        except Exception as error:
            # At the detached worker boundary, persist and re-raise: never silently
            # lose the failure or blindly repeat a possibly successful send.
            state["callback"]["error"] = f"{type(error).__name__}: {error}"
            state["callback"]["error_at"] = time.time()
            save_status(state)
            logger.error("Callback pending recovery: %s", error)
            raise
        else:
            state["callback"].pop("error", None)
            state["callback"].pop("error_at", None)
            save_status(state)
            logger.info(
                "Callback started in original task: %s", state["callback"]["turn_id"]
            )


def main():
    """Internal entry point; public callers use start_job(), notify(), or retry_callback()."""
    os.umask(0o077)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    work(Path(os.environ["CODEX_CALLBACK_DIRECTORY"]))


if __name__ == "__main__":
    main()
