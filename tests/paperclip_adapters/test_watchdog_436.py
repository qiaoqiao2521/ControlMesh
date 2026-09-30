"""Offline checks; all CLI calls mocked, all watchdog state kept in temporary homes."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

BASE = Path(__file__).parent
FIXED = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def load_watchdog(source, home):
    module = types.ModuleType("watchdog_offline")
    with patch.object(Path, "home", return_value=home):
        exec(compile(source.read_text(), str(source), "exec"), module.__dict__)
    module.now = lambda: FIXED
    return module


class WatchdogChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="watchdog-offline-", dir=BASE)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.w = load_watchdog(BASE.parents[1] / "scripts/paperclip/cron-watchdog-436.py", self.home)
        self.w.NOTIFICATION_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        self.w.NOTIFICATION_CONFIG.write_text(json.dumps({"chat_id": "oc_offline_test"}))

    def test_cli_receipt_required_and_identity_pinned(self):
        samples = [
            (0, '{"ok":true,"data":{"message_id":"om_test"}}', True),
            (0, '{"code":0,"data":{"message_id":"om_test"}}', True),
            (0, '{"ok":true,"data":{"data":{"message_id":"om_test"}}}', True),
            (0, '{"ok":false,"data":{"message_id":"om_test"}}', False),
            (0, '{"code":1,"data":{"message_id":"om_test"}}', False),
            (0, '{"ok":true}', False),
            (0, 'not-json', False),
            (1, '{"ok":true,"data":{"message_id":"om_test"}}', False),
        ]
        keys = []
        for exit_code, output, expected in samples:
            with self.subTest(exit_code=exit_code, output=output):
                with patch.object(self.w.subprocess, "run", return_value=types.SimpleNamespace(
                    returncode=exit_code, stdout=output
                )) as cli:
                    self.assertIs(self.w.notify_alert("offline sample", "stalled:job"), expected)
                    argv = cli.call_args.args[0]
                    self.assertEqual(argv[0], "/usr/sbin/runuser")
                    self.assertEqual(argv[argv.index("-u") + 1], "agent436")
                    self.assertEqual(argv[argv.index("--profile") + 1], "cm436")
                    self.assertEqual(argv[argv.index("--as") + 1], "bot")
                    self.assertEqual(argv[argv.index("--chat-id") + 1], "oc_offline_test")
                    keys.append(argv[argv.index("--idempotency-key") + 1])
                    self.assertNotIn("shell", cli.call_args.kwargs)
        self.assertEqual(len(set(keys)), 1)
        self.assertLessEqual(len(keys[0]), 50)
        for error in [subprocess.TimeoutExpired("mock", 30), OSError("mock")]:
            with patch.object(self.w.subprocess, "run", side_effect=error):
                self.assertFalse(self.w.notify_alert("offline sample", "stalled:job"))

    def test_missing_chat_does_not_invoke_cli(self):
        self.w.NOTIFICATION_CONFIG.unlink()
        with patch.object(self.w.subprocess, "run") as cli:
            self.assertFalse(self.w.notify_alert("offline sample", "job"))
            cli.assert_not_called()

    def test_disabled_jobs_and_clean_daily_remain_silent(self):
        jobs = [{"id": f"job-{i}", "enabled": False, "schedule": "0 * * * *"} for i in range(19)]
        self.w.REGISTRY.write_text(json.dumps({"jobs": jobs}))
        before = self.w.REGISTRY.read_bytes()
        with patch.object(self.w.subprocess, "run") as cli, contextlib.redirect_stdout(io.StringIO()):
            self.w.run_once(False)
            self.w.run_daily(False)
            cli.assert_not_called()
        self.assertEqual(self.w.REGISTRY.read_bytes(), before)
        self.assertEqual(list(self.w.STATE.glob("*.json")), [])

    def test_failed_stall_notification_is_not_marked(self):
        job = {"id": "job", "enabled": True, "schedule": "0 */1 * * *", "last_run_at": None}
        self.w.save_state("job", {"enabled_since": "2026-10-01T00:00:00+00:00", "seen_last_run_at": None, "consecutive_failures": 0})
        with patch.object(self.w, "notify_alert", return_value=False):
            actions = self.w.judge_job(job, False)
        self.assertEqual(actions[0][0], "stalled")
        self.assertIsNone(json.loads((self.w.STATE / "job.json").read_text()).get("last_alert_date"))

    def test_artifact_delivery_failure_keeps_notification_unmarked(self):
        self.w.ARTIFACTS.write_text(json.dumps({"output": {"path": str(self.home / "missing-output")}}))
        with patch.object(self.w, "notify_alert", return_value=False) as notify:
            actions = self.w.check_artifacts(False)
            self.assertEqual(actions[0][0], "artifact")
            notify.assert_called_once()
            self.assertFalse((self.w.STATE / "artifact_output.json").exists())
        with patch.object(self.w, "notify_alert", return_value=True) as notify:
            self.w.check_artifacts(False)
            self.w.check_artifacts(False)
            notify.assert_called_once()
            state = json.loads((self.w.STATE / "artifact_output.json").read_text())
            self.assertEqual(state["last_alert_date"], "2026-10-01")


if __name__ == "__main__":
    unittest.main(verbosity=2)
