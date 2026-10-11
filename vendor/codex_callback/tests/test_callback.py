"""Exercise duplicate prevention, task scheduling, and real process outcomes."""

import copy
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_callback.delivery import UncertainDelivery, deliver
from codex_callback.jobs import read_status, retry_callback, save_status, start_job
from codex_callback.worker import run_process


def make_state(directory):
    return {
        "id": "test-event",
        "thread_id": "original-task",
        "socket_path": "/unused/socket",
        "directory": str(directory),
        "cwd": str(directory),
        "created_at": time.time(),
        "outcome": "completed",
        "returncode": 0,
        "followup": "Inspect this result",
        "callback_wait_seconds": 5,
        "callback": {"status": "pending"},
        "command": [sys.executable, "-c", "print('test output')"],
        "timeout_seconds": 2,
    }


class FakeClient:
    """Represent a daemon, including races with the desktop queue consumer."""

    def __init__(self, active=False, auto_consume=False, drop_after_add=False):
        self.active = active
        self.auto_consume = auto_consume
        self.drop_after_add = drop_after_add
        self.items = []
        self.turn_id = None
        self.calls = []
        self.waits = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read_thread(self, thread_id):
        return {"status": {"type": "active" if self.active else "idle"}}

    def queue_items(self, thread_id):
        return iter(self.items)

    def find_turn(self, *args):
        return self.turn_id

    def wait_for_change(self, *args):
        self.waits += 1
        self.active = False
        if self.auto_consume:
            self.items.clear()
            self.turn_id = "desktop-started-turn"

    def request(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == "thread/resume":
            return {}
        if method == "thread/queue/add":
            item = {"id": "queue-entry", **params}
            self.items.append(item)
            if self.drop_after_add:
                self.drop_after_add = False
                raise ConnectionError("lost acknowledgement")
            return {"queuedSubmission": item}
        if method == "thread/queue/start":
            if self.active:
                raise AssertionError("must not start over an active task")
            self.items.clear()
            self.turn_id = "callback-turn"
            return {"turn": {"id": self.turn_id}}
        raise AssertionError(method)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state = make_state(Path(self.temporary.name))
        self.client = FakeClient()

    def send(self):
        deliver(self.state, save_status, lambda path: self.client)

    def test_idle_starts_original_task_without_settings_overrides(self):
        self.send()
        self.assertEqual(self.state["callback"]["status"], "started")
        for method, params in self.client.calls:
            self.assertEqual(params["threadId"], "original-task")
            self.assertNotIn("model", params)
            self.assertNotIn("approvalPolicy", params)
            self.assertNotIn("cwd", params)
        self.assertEqual(
            [m for m, _ in self.client.calls],
            ["thread/resume", "thread/queue/add", "thread/queue/start"],
        )

    def test_busy_task_waits_for_event_before_starting(self):
        self.client.active = True
        self.send()
        self.assertEqual(self.client.waits, 1)
        self.assertEqual(self.state["callback"]["status"], "started")

    def test_desktop_can_consume_queue_first(self):
        self.client = FakeClient(active=True, auto_consume=True)
        self.send()
        self.assertEqual(self.state["callback"]["turn_id"], "desktop-started-turn")
        self.assertNotIn("thread/queue/start", [m for m, _ in self.client.calls])

    def test_lost_add_ack_is_reconciled_without_duplicate(self):
        self.client.drop_after_add = True
        with self.assertRaises(ConnectionError):
            self.send()
        self.assertEqual(
            read_status(self.state["directory"])["callback"]["status"], "sending"
        )
        self.send()
        self.assertEqual([m for m, _ in self.client.calls].count("thread/queue/add"), 1)

    def test_uncertain_delivery_is_not_blindly_repeated(self):
        self.state["callback"]["status"] = "sending"
        self.state["callback_wait_seconds"] = 0.01
        with self.assertRaises(UncertainDelivery):
            self.send()
        self.assertNotIn("thread/queue/add", [m for m, _ in self.client.calls])

    def test_queue_consumption_can_precede_history_visibility(self):
        self.client = FakeClient(active=True, auto_consume=True)
        with patch.object(self.client, "find_turn", side_effect=[None, "delayed-turn"]):
            self.send()
        self.assertEqual(self.state["callback"]["turn_id"], "delayed-turn")
        self.assertEqual(self.state["callback"]["receipt_source"], "history")
        self.assertEqual([m for m, _ in self.client.calls].count("thread/queue/add"), 1)

    def test_lost_start_ack_uses_history_receipt(self):
        original = self.client.request

        def lose_reply(method, params):
            result = original(method, params)
            if method == "thread/queue/start":
                raise ConnectionError("lost start acknowledgement")
            return result

        self.client.request = lose_reply
        with self.assertRaises(ConnectionError):
            self.send()
        self.client.request = original
        self.send()
        self.assertEqual(self.state["callback"]["turn_id"], "callback-turn")
        self.assertEqual(
            [m for m, _ in self.client.calls].count("thread/queue/start"), 1
        )

    def test_completed_callback_is_noop_and_never_reruns_training(self):
        self.send()
        count = len(self.client.calls)
        self.send()
        with patch("codex_callback.jobs._spawn") as spawn:
            retry_callback(self.state["directory"])
        spawn.assert_not_called()
        self.assertEqual(len(self.client.calls), count)

    def test_retry_only_spawns_callback_worker(self):
        save_status(self.state)
        with patch("codex_callback.jobs._spawn") as spawn:
            retry_callback(self.state["directory"])
        spawn.assert_called_once_with(Path(self.state["directory"]))


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state = make_state(Path(self.temporary.name))

    def run_code(self, code, timeout=2):
        self.state["command"] = [sys.executable, "-c", code]
        self.state["timeout_seconds"] = timeout
        run_process(self.state)
        return read_status(self.state["directory"])

    def test_success_captures_log_and_exit_code(self):
        state = self.run_code("print('training complete')")
        self.assertEqual((state["outcome"], state["returncode"]), ("completed", 0))
        self.assertIn(
            "training complete", (Path(self.state["directory"]) / "job.log").read_text()
        )

    def test_failure_preserves_traceback(self):
        state = self.run_code("raise RuntimeError('deliberate failure')")
        self.assertEqual((state["outcome"], state["returncode"]), ("failed", 1))
        self.assertIn(
            "deliberate failure",
            (Path(self.state["directory"]) / "job.log").read_text(),
        )

    def test_signal_exit_is_failure(self):
        state = self.run_code("import os, signal; os.kill(os.getpid(), signal.SIGTERM)")
        self.assertEqual(
            (state["outcome"], state["returncode"]), ("failed", -signal.SIGTERM)
        )

    def test_timeout_stops_process(self):
        state = self.run_code("import time; time.sleep(30)", timeout=0.1)
        self.assertEqual(state["outcome"], "timed_out")
        self.assertLess(state["returncode"], 0)

    def test_missing_executable_is_recorded(self):
        self.state["command"] = ["/nonexistent/callback-test-python"]
        run_process(self.state)
        self.assertEqual(self.state["outcome"], "failed")
        self.assertIn("process_error", self.state)

    def test_supervisor_cancellation_records_outcome(self):
        state = self.run_code(
            "import os, signal, time; os.kill(os.getppid(), signal.SIGTERM); time.sleep(30)"
        )
        self.assertEqual(state["outcome"], "cancelled")
        self.assertLess(state["returncode"], 0)

    def test_timeout_kills_descendant_that_ignores_sigterm(self):
        child = (
            "import signal,time; from pathlib import Path; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "Path('ready').touch(); time.sleep(0.6); Path('escaped').touch()"
        )
        code = f"import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(30)"
        state = self.run_code(code, timeout=0.3)
        self.assertEqual(state["outcome"], "timed_out")
        self.assertTrue((Path(self.state["directory"]) / "ready").exists())
        time.sleep(0.6)
        self.assertFalse((Path(self.state["directory"]) / "escaped").exists())

    def test_shell_string_is_rejected_before_launch(self):
        with self.assertRaises(ValueError):
            start_job("python train.py", cwd=".", followup="Inspect")


if __name__ == "__main__":
    unittest.main()
