"""Verify delivery reconciliation with an isolated Codex queue peer."""

# ruff: noqa: INP001, E402, PT009, PT027
# Standalone unittest fixtures match the pinned upstream delivery tests.

from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


RUNTIME = Path(__file__).resolve().parents[2] / "vendor/codex_callback/runtime"
sys.path.insert(0, str(RUNTIME))

from codex_callback.client import RpcError
from codex_callback.delivery import UncertainDelivery, deliver
from codex_callback.jobs import read_status, save_status


class QueuePeer:
    """Consume a submission exactly between the queue read and start request."""

    def __init__(self, *, consume=True, receipt=True, active=False):
        self.consume = consume
        self.receipt = receipt
        self.active = active
        self.items = []
        self.calls = []
        self.receipt_queries = []
        self.consumed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read_thread(self, thread_id):
        return {"status": {"type": "active" if self.consumed and self.active else "idle"}}

    def queue_items(self, thread_id):
        return iter(self.items)

    def find_turn(self, thread_id, event_id, created_at):
        self.receipt_queries.append((thread_id, event_id, created_at))
        return "desktop-turn" if self.consumed and self.receipt else None

    def wait_for_change(self, *args):
        raise AssertionError("a missing queue entry must be reconciled immediately")

    def request(self, method, params):
        self.calls.append((method, params))
        if method == "thread/resume":
            return {}
        if method == "thread/queue/add":
            item = {"id": "queue-entry", **params}
            self.items.append(item)
            return {"queuedSubmission": item}
        if method == "thread/queue/start":
            if self.consume:
                self.items.clear()
                self.consumed = True
                message = "queued submission not found: queue-entry"
            else:
                message = "cannot start this submission"
            raise RpcError(method, {"code": -32600, "message": message})
        raise AssertionError(method)


class DeliveryRaceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = {
            "id": "completion-event",
            "thread_id": "original-thread",
            "socket_path": "/unused/socket",
            "directory": str(self.directory),
            "cwd": str(self.directory),
            "created_at": time.time(),
            "outcome": "completed",
            "returncode": 0,
            "followup": "Review the handoff once.",
            "callback_wait_seconds": 1,
            "callback": {"status": "pending"},
        }

    def send(self, peer):
        deliver(self.state, save_status, lambda _: peer)

    def assert_single_submission(self, peer):
        methods = [method for method, _ in peer.calls]
        self.assertEqual(methods.count("thread/queue/add"), 1)
        self.assertEqual(methods.count("thread/queue/start"), 1)

    def test_app_consumption_reconciles_after_turn_already_finished(self):
        peer = QueuePeer()
        self.send(peer)
        receipt = read_status(self.directory)["callback"]
        self.assertEqual(receipt["status"], "started")
        self.assertEqual(receipt["turn_id"], "desktop-turn")
        self.assertEqual(receipt["receipt_source"], "history")
        self.assertEqual(peer.receipt_queries, [
            (self.state["thread_id"], self.state["id"], self.state["created_at"])
        ])
        self.assert_single_submission(peer)

    def test_app_consumption_reconciles_while_turn_is_active(self):
        peer = QueuePeer(active=True)
        self.send(peer)
        self.assertEqual(self.state["callback"]["turn_id"], "desktop-turn")
        self.assertEqual(self.state["callback"]["receipt_source"], "history")
        self.assert_single_submission(peer)

    def test_app_consumption_waits_for_delayed_history_receipt(self):
        peer = QueuePeer()
        with (
            patch.object(peer, "find_turn", side_effect=[None, "desktop-turn"]) as find,
            patch("codex_callback.delivery.time.sleep"),
        ):
            self.send(peer)
        self.assertEqual(find.call_count, 2)
        self.assertEqual(self.state["callback"]["turn_id"], "desktop-turn")
        self.assert_single_submission(peer)

    def test_missing_queue_without_receipt_stays_uncertain_without_resend(self):
        peer = QueuePeer(receipt=False)
        with (
            patch("codex_callback.delivery.time.monotonic", side_effect=[0, 0, 0, 2]),
            self.assertRaises(UncertainDelivery),
        ):
            self.send(peer)
        self.assertEqual(read_status(self.directory)["callback"]["status"], "queued")
        self.assertNotIn("turn_id", self.state["callback"])
        self.assert_single_submission(peer)

    def test_existing_queue_preserves_start_error_without_false_success(self):
        peer = QueuePeer(consume=False)
        with self.assertRaises(RpcError) as caught:
            self.send(peer)
        self.assertEqual(caught.exception.error["message"], "cannot start this submission")
        self.assertEqual(self.state["callback"]["status"], "queued")
        self.assertEqual(peer.receipt_queries, [])
        self.assert_single_submission(peer)


if __name__ == "__main__":
    unittest.main()
