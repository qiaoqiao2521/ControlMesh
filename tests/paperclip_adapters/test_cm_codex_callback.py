"""Test local completion receipts without starting a worker or touching services."""

# ruff: noqa: INP001, E402, PT009, PT027
# Standalone stdlib tests match upstream; the CLI loads the pinned runtime first.

from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
m = types.ModuleType("cm_codex_callback")
m.__file__ = str(ROOT / "scripts/paperclip/cm-codex-callback")
SourceFileLoader(m.__name__, m.__file__).exec_module(m)
from codex_callback import jobs

COMPANY = "00000000-0000-4000-8000-000000000001"
ISSUE = "00000000-0000-4000-8000-000000000002"
THREAD = "00000000-0000-4000-8000-000000000003"
RUN = "00000000-0000-4000-8000-000000000004"
OTHER = "00000000-0000-4000-8000-000000000005"


class BridgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cwd = self.root / "work"
        self.cwd.mkdir()
        self.state = self.root / "state"
        self.socket = self.root / "socket-link"
        self.handoff = self.cwd / "handoff.json"
        self.handoff.write_text('{"result":"ready_for_review"}\n')
        self.loaded = [THREAD]
        self.thread = {"id": THREAD, "cwd": str(self.cwd), "canAcceptDirectInput": True}
        self.pages = None
        self.calls = []
        owner = self

        class Native:
            def __init__(self, socket):
                owner.calls.append(("connect", str(socket)))
                self.index = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def request(self, method, params):
                owner.calls.append((method, params))
                if method != "thread/loaded/list":
                    raise AssertionError("preflight must not write to native queue")
                if owner.pages is not None:
                    page = owner.pages[self.index]
                    self.index += 1
                    return page
                return {"data": owner.loaded, "nextCursor": None}

            def read_thread(self, thread_id):
                owner.calls.append(("thread/read", thread_id))
                return dict(owner.thread)

        self.addCleanup(patch.stopall)
        patch.object(m, "CodexClient", Native).start()
        self.spawn = patch.object(jobs, "_spawn", return_value=12345).start()
        self.notify = patch.object(m, "notify", wraps=jobs.notify).start()

    def bind(self, **extra):
        fields = {"thread_id": THREAD, "cwd": self.cwd, "socket_path": self.socket,
                  "state_dir": self.state, **extra}
        return m.bind(COMPANY, ISSUE, **fields)

    def send(self, outcome="completed", **extra):
        return m.notify_completion(COMPANY, ISSUE, RUN, outcome, self.handoff,
                                   state_dir=self.state, **extra)

    def event_directory(self):
        return self.state / COMPANY / ISSUE / "events" / RUN

    def callback(self):
        return next((self.event_directory() / "callbacks").iterdir())

    def test_bind_freezes_identity_and_replay_does_not_mutate_it(self):
        result = self.bind()
        self.assertTrue(result["bound"])
        path = self.state / COMPANY / ISSUE / "binding.json"
        before = path.read_bytes()
        self.assertTrue(self.bind()["replayed"])
        with self.assertRaisesRegex(ValueError, "binding_conflict"):
            self.bind(thread_id=OTHER)
        self.assertEqual(path.read_bytes(), before)
        self.spawn.assert_not_called()

    def test_bind_uses_original_environment_thread(self):
        with patch.dict(m.os.environ, {"CODEX_THREAD_ID": THREAD}):
            result = self.bind(thread_id=None)
        self.assertEqual(result["thread_id"], THREAD)

    def test_bind_rejects_unloaded_thread(self):
        self.loaded = []
        with self.assertRaisesRegex(ValueError, "native_thread_not_loaded"):
            self.bind()
        self.assertFalse((self.state / COMPANY / ISSUE / "binding.json").exists())

    def test_bind_rejects_wrong_native_identity(self):
        self.thread["id"] = OTHER
        with self.assertRaisesRegex(ValueError, "native_thread_identity_mismatch"):
            self.bind()

    def test_bind_rejects_wrong_native_cwd(self):
        self.thread["cwd"] = str(self.root)
        with self.assertRaisesRegex(ValueError, "native_thread_cwd_mismatch"):
            self.bind()

    def test_bind_requires_positive_input_capability(self):
        for value in (False, None):
            self.thread["canAcceptDirectInput"] = value
            with self.assertRaisesRegex(ValueError, "native_thread_input_unavailable"):
                self.bind()

    def test_bind_follows_loaded_list_pagination(self):
        self.pages = [{"data": [], "nextCursor": "next"},
                      {"data": [THREAD], "nextCursor": None}]
        self.assertTrue(self.bind()["bound"])
        requests = [params for name, params in self.calls if name == "thread/loaded/list"]
        self.assertEqual([p["cursor"] for p in requests], [None, "next"])

    def test_binding_preserves_logical_socket_path(self):
        first = self.root / "socket-a"
        self.socket.symlink_to(first)
        result = self.bind()
        self.assertEqual(result["socket_path"], str(self.socket))
        self.assertNotEqual(result["socket_path"], str(first))

    def test_notify_creates_once_and_freezes_handoff_hash(self):
        self.bind()
        first = self.send()
        second = self.send()
        self.assertEqual(first["phase"], "callback_created")
        self.assertTrue(second["replayed"])
        self.assertEqual(first["handoff"], second["handoff"])
        self.notify.assert_called_once()
        self.spawn.assert_called_once()
        state = jobs.read_status(self.callback())
        self.assertEqual(state["thread_id"], THREAD)
        self.assertIn(first["handoff"]["sha256"], state["followup"])
        self.assertFalse(first["business_accepted"])
        self.assertFalse(first["followup_complete"])

    def test_notify_rejects_changed_completion_or_handoff(self):
        self.bind()
        self.send()
        with self.assertRaisesRegex(ValueError, "completion_conflict"):
            self.send(outcome="failed")
        self.handoff.write_text("changed result")
        with self.assertRaisesRegex(ValueError, "completion_conflict"):
            self.send()
        self.notify.assert_called_once()

    def test_notify_rejects_handoff_outside_bound_cwd(self):
        self.bind()
        outside = self.root / "outside.json"
        outside.write_text("outside")
        with self.assertRaisesRegex(ValueError, "handoff_outside_bound_cwd"):
            m.notify_completion(COMPANY, ISSUE, RUN, "completed", outside, state_dir=self.state)
        self.notify.assert_not_called()

    def test_notify_rejects_symlink_handoff_escape(self):
        self.bind()
        outside = self.root / "outside.json"
        outside.write_text("outside")
        self.handoff.unlink()
        self.handoff.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "handoff_symlink_refused"):
            self.send()
        self.notify.assert_not_called()

    def test_notify_rechecks_original_thread_before_any_creation(self):
        self.bind()
        self.loaded = []
        with self.assertRaisesRegex(ValueError, "native_thread_not_loaded"):
            self.send()
        self.notify.assert_not_called()
        self.assertFalse((self.event_directory() / "event.json").exists())

    def test_unknown_before_creation_is_not_automatically_retried(self):
        self.bind()
        self.notify.side_effect = OSError("simulated unavailable creator")
        with self.assertRaisesRegex(ValueError, "notify_result_unknown"):
            self.send()
        result = self.send()
        self.assertEqual(result["phase"], "needs_reconciliation")
        self.assertEqual(result["callback"]["status"], "unknown")
        self.notify.assert_called_once()
        self.spawn.assert_not_called()

    def test_lost_creation_ack_keeps_pending_worker_uncertain(self):
        self.bind()

        def lose_ack(**kwargs):
            jobs.notify(**kwargs)
            raise OSError("simulated lost acknowledgment")

        self.notify.side_effect = lose_ack
        with self.assertRaisesRegex(ValueError, "notify_result_unknown"):
            self.send()
        result = self.send()
        self.assertEqual(result["phase"], "needs_reconciliation")
        self.assertEqual(result["callback"]["status"], "pending")
        self.notify.assert_called_once()
        self.spawn.assert_called_once()
        event = json.loads((self.event_directory() / "event.json").read_text())
        self.assertEqual(event["phase"], "needs_reconciliation")

    def test_worker_progress_recovers_existing_callback_after_lost_ack(self):
        self.test_lost_creation_ack_keeps_pending_worker_uncertain()
        state = jobs.read_status(self.callback())
        state["worker_pid"] = 12345
        state["callback"].update(status="queued", queue_id="queue-one")
        jobs.save_status(state)
        result = self.send()
        self.assertEqual(result["phase"], "callback_created")
        self.assertEqual(result["callback"]["queue_id"], "queue-one")
        self.notify.assert_called_once()
        self.spawn.assert_called_once()

    def test_started_receipt_is_not_followup_or_business_completion(self):
        self.bind()
        self.send()
        state = jobs.read_status(self.callback())
        state["callback"].update(status="started", queue_id="queue-one", turn_id="turn-one")
        jobs.save_status(state)
        result = m.status(COMPANY, ISSUE, RUN, state_dir=self.state)
        self.assertEqual(result["callback"]["turn_id"], "turn-one")
        self.assertFalse(result["business_accepted"])
        self.assertFalse(result["followup_complete"])
        self.notify.assert_called_once()

    def test_started_status_without_receipt_is_rejected(self):
        self.bind()
        self.send()
        state = jobs.read_status(self.callback())
        state["callback"].update(status="started")
        jobs.save_status(state)
        with self.assertRaisesRegex(ValueError, "callback_receipt_missing"):
            m.status(COMPANY, ISSUE, RUN, state_dir=self.state)

    def test_wrong_callback_thread_is_rejected_without_resend(self):
        self.bind()
        self.send()
        state = jobs.read_status(self.callback())
        state["thread_id"] = OTHER
        jobs.save_status(state)
        with self.assertRaisesRegex(ValueError, "callback_identity_mismatch"):
            self.send()
        self.notify.assert_called_once()

    def test_failed_outcome_stays_failed(self):
        self.bind()
        result = self.send(outcome="failed")
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(jobs.read_status(self.callback())["outcome"], "failed")
        self.assertFalse(result["business_accepted"])

    def test_partial_callback_state_does_not_create_another_callback(self):
        self.bind()
        self.notify.side_effect = OSError("simulated unavailable creator")
        with self.assertRaises(ValueError):
            self.send()
        partial = self.event_directory() / "callbacks" / OTHER
        partial.mkdir(mode=0o700)
        result = self.send()
        self.assertEqual(result["phase"], "needs_reconciliation")
        self.notify.assert_called_once()

    def test_bind_rejects_public_or_symlink_state_directory(self):
        self.state.mkdir(mode=0o755)
        with self.assertRaisesRegex(ValueError, "private_state_directory_required"):
            self.bind()
        self.state.rmdir()
        self.state.symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, "state_symlink_refused"):
            self.bind()


if __name__ == "__main__":
    unittest.main()
