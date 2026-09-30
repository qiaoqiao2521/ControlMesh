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

    def native_setup(self, enabled=False, variables=None):
        context = self.home / ".paperclip/context.json"
        context.parent.mkdir(parents=True, exist_ok=True)
        context.write_text(json.dumps({"profiles": {"cm-other": {
            "companyId": "offline-company", "apiBase": "http://127.0.0.1:3100"}}}))
        clock = {"bin": "/offline/paperclip", "context": str(context), "profile": "cm-other",
                 "company_id": "offline-company", "expected_job_ids": ["job"],
                 "activated_at": "2026-10-01T09:00:00+00:00"}
        self.w.NOTIFICATION_CONFIG.write_text(json.dumps({"native_clock": clock}))
        self.w.REGISTRY.write_text(json.dumps({"jobs": [{"id": "job", "enabled": True,
            "schedule": "0 */1 * * *", "last_run_at": "2026-09-01T00:00:00+00:00",
            "last_run_status": "error"}]}))
        routine = {"id": "routine-id", "companyId": "offline-company", "status": "active",
                   "title": "job", "variables": variables if variables is not None else [
                       {"name": "cmJobId", "defaultValue": "job"}],
                   "triggers": [{"id": "trigger-id", "kind": "schedule", "enabled": enabled}]}
        return clock, routine

    def test_other_host_requires_and_uses_explicit_lark_route(self):
        self.native_setup()
        config = json.loads(self.w.NOTIFICATION_CONFIG.read_text())
        config["chat_id"] = "oc_other_host"
        self.w.NOTIFICATION_CONFIG.write_text(json.dumps(config))
        with patch.object(self.w.subprocess, "run") as cli:
            self.assertFalse(self.w.notify_alert("offline", "job"))
            cli.assert_not_called()
        config["lark"] = {"user": "root", "home": "/root", "path": "/offline/bin:/usr/bin",
                          "cli": "/offline/lark-cli", "profile": "cm-other"}
        self.w.NOTIFICATION_CONFIG.write_text(json.dumps(config))
        with patch.object(self.w.subprocess, "run", return_value=types.SimpleNamespace(
                returncode=0, stdout='{"data":{"message_id":"om_other"}}')) as cli:
            self.assertTrue(self.w.notify_alert("offline", "job"))
            argv = cli.call_args.args[0]
            self.assertEqual(argv[argv.index("-u") + 1], "root")
            self.assertIn("HOME=/root", argv)
            self.assertIn("PATH=/offline/bin:/usr/bin", argv)
            self.assertIn("/offline/lark-cli", argv)
            self.assertEqual(argv[argv.index("--profile") + 1], "cm-other")
            self.assertNotIn("agent436", argv)

    def test_native_paused_skips_old_failures_but_checks_artifacts(self):
        _, routine = self.native_setup()
        self.w.save_state("job", {"enabled_since": "2026-09-01T00:00:00+00:00",
                                  "consecutive_failures": 9})
        before = self.w.REGISTRY.read_bytes()
        self.w.ARTIFACTS.write_text(json.dumps({"independent": {"path": str(self.home / "missing")}}))
        with patch.object(self.w, "native_cli", return_value=[routine]) as snapshot, \
                patch.object(self.w, "judge_job") as judge, \
                patch.object(self.w, "notify_alert", return_value=False) as notify, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.w.run_once(False)
        snapshot.assert_called_once()
        judge.assert_not_called()
        notify.assert_called_once()
        self.assertIn("0 active, 1 paused", output.getvalue())
        self.assertIn("[artifact]", output.getvalue())
        self.assertEqual(self.w.REGISTRY.read_bytes(), before)
        state = json.loads((self.w.STATE / "job.json").read_text())
        self.assertEqual(state["consecutive_failures"], 9)
        self.assertEqual(state["enabled_since"], "2026-09-01T00:00:00+00:00")
        self.assertEqual(state["native_paused_at"], FIXED.isoformat())

    def test_native_unknown_never_falls_back_or_reports_clean(self):
        _, routine = self.native_setup(variables=[])
        for payload in [ValueError("offline API error"), [routine]]:
            with self.subTest(payload=type(payload).__name__):
                effect = {"side_effect": payload} if isinstance(payload, Exception) else {"return_value": payload}
                with patch.object(self.w, "native_cli", **effect), \
                        patch.object(self.w, "judge_job") as judge, \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    self.w.run_once(False)
                judge.assert_not_called()
                self.assertIn("native clock unknown", output.getvalue())
                self.assertNotIn("pass clean", output.getvalue())

    def test_corrupt_declared_configuration_is_unknown_not_legacy(self):
        self.native_setup()
        for body in ["not-json", "[]", "null"]:
            self.w.NOTIFICATION_CONFIG.write_text(body)
            with patch.object(self.w, "judge_job") as judge, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.w.run_once(False)
            judge.assert_not_called()
            self.assertIn("native clock unknown", output.getvalue())
            self.assertNotIn("pass clean", output.getvalue())

    def test_native_cutover_uses_only_new_manual_receipts_and_skip_is_not_failure(self):
        clock, routine = self.native_setup(enabled=True)
        data = json.loads(self.w.REGISTRY.read_text())
        self.w.save_state("job", {"enabled_since": "2026-09-01T00:00:00+00:00", "consecutive_failures": 9})
        with patch.object(self.w, "native_cli", return_value=[routine]):
            jobs, _ = self.w.observed_jobs(data)
        with patch.object(self.w, "notify_alert") as notify:
            self.assertEqual(self.w.judge_job(jobs[0], False)[0][0], "stalled")
        # The stall reflects the declared three-hour native expectation, not nine old failures.
        state = json.loads((self.w.STATE / "job.json").read_text())
        self.assertEqual(state["consecutive_failures"], 0)
        self.assertEqual(state["enabled_since"], clock["activated_at"])
        for status in ("skipped_quiet_hours", "quiet_skipped"):
            with self.subTest(status=status):
                data["jobs"][0].update(manual_run_at="2026-10-01T11:30:00+00:00", manual_run_status=status)
                with patch.object(self.w, "native_cli", return_value=[routine]):
                    jobs, observation = self.w.observed_jobs(data)
                self.assertNotIn("unknown", observation)
                with patch.object(self.w, "notify_alert") as notify:
                    self.assertEqual(self.w.judge_job(jobs[0], False), [])
                    notify.assert_not_called()
                self.assertEqual(json.loads((self.w.STATE / "job.json").read_text())["consecutive_failures"], 0)

    def test_native_pause_verifies_real_trigger_and_preserves_old_registry(self):
        clock, routine = self.native_setup(enabled=True)
        data = json.loads(self.w.REGISTRY.read_text())
        with patch.object(self.w, "native_cli", return_value=[routine]):
            job = self.w.observed_jobs(data)[0][0]
        paused = dict(routine, triggers=[{"id": "trigger-id", "kind": "schedule", "enabled": False}])
        before = self.w.REGISTRY.read_bytes()
        results = [types.SimpleNamespace(returncode=0, stdout='{}'),
                   types.SimpleNamespace(returncode=0, stdout=json.dumps([paused]))]
        with patch.object(self.w.subprocess, "run", side_effect=results) as cli:
            self.assertTrue(self.w.registry_pause("job", job))
        argv = cli.call_args_list[0].args[0]
        self.assertEqual(argv[:4], [clock["bin"], "routine", "trigger:update", "trigger-id"])
        self.assertNotIn("routine-id", argv)
        self.assertEqual(self.w.REGISTRY.read_bytes(), before)
        for result in [types.SimpleNamespace(returncode=1, stdout=''),
                       types.SimpleNamespace(returncode=0, stdout='{}')]:
            with patch.object(self.w.subprocess, "run", return_value=result):
                self.assertFalse(self.w.registry_pause("job", job))

    def test_native_activation_grace_rejects_pre_cutover_manual_watermark(self):
        clock, routine = self.native_setup(enabled=True)
        clock["activated_at"] = "2026-10-01T11:50:00+00:00"
        self.w.NOTIFICATION_CONFIG.write_text(json.dumps({"native_clock": clock}))
        data = json.loads(self.w.REGISTRY.read_text())
        data["jobs"][0].update(manual_run_at="2026-10-01T10:00:00+00:00", manual_run_status="error")
        self.w.save_state("job", {"enabled_since": "2026-09-01T00:00:00+00:00", "consecutive_failures": 9})
        with patch.object(self.w, "native_cli", return_value=[routine]):
            job = self.w.observed_jobs(data)[0][0]
        self.assertIsNone(job["last_run_at"])
        with patch.object(self.w, "notify_alert") as notify:
            self.assertEqual(self.w.judge_job(job, False), [])
            notify.assert_not_called()
        self.assertEqual(json.loads((self.w.STATE / "job.json").read_text())["consecutive_failures"], 0)

    def test_native_pause_failure_cannot_claim_auto_paused(self):
        clock, routine = self.native_setup(enabled=True)
        data = json.loads(self.w.REGISTRY.read_text())
        data["jobs"][0].update(manual_run_at="2026-10-01T11:30:00+00:00", manual_run_status="error")
        with patch.object(self.w, "native_cli", return_value=[routine]):
            job = self.w.observed_jobs(data)[0][0]
        self.w.save_state("job", {"native_clock_epoch": clock["activated_at"],
                                  "enabled_since": clock["activated_at"], "consecutive_failures": 1,
                                  "seen_last_run_at": "2026-10-01T10:30:00+00:00"})
        with patch.object(self.w.subprocess, "run", return_value=types.SimpleNamespace(returncode=1, stdout='')), \
                patch.object(self.w, "notify_alert", return_value=False):
            actions = self.w.judge_job(job, False)
        self.assertEqual(actions[0][0], "pause_failed")
        self.assertNotIn("paused_by", json.loads((self.w.STATE / "job.json").read_text()))

    def test_native_resume_excludes_pause_time_and_old_manual_receipt(self):
        clock, routine = self.native_setup()
        data = json.loads(self.w.REGISTRY.read_text())
        data["jobs"][0].update(manual_run_at="2026-10-01T11:30:00+00:00", manual_run_status="error")
        self.w.save_state("job", {"native_clock_epoch": clock["activated_at"],
                                  "enabled_since": clock["activated_at"], "consecutive_failures": 9})
        with patch.object(self.w, "native_cli", return_value=[routine]):
            self.w.observed_jobs(data)
        routine["triggers"][0]["enabled"] = True
        self.w.now = lambda: datetime(2026, 10, 1, 12, 5, tzinfo=timezone.utc)
        with patch.object(self.w, "native_cli", return_value=[routine]):
            job = self.w.observed_jobs(data)[0][0]
        with patch.object(self.w, "notify_alert") as notify:
            self.assertEqual(self.w.judge_job(job, False), [])
            notify.assert_not_called()
        state = json.loads((self.w.STATE / "job.json").read_text())
        self.assertEqual(state["enabled_since"], FIXED.isoformat())
        self.assertEqual(state["consecutive_failures"], 0)

    def test_native_daily_is_local_even_with_old_failure_state(self):
        _, routine = self.native_setup()
        self.w.save_state("job", {"consecutive_failures": 9})
        with patch.object(self.w, "native_cli", return_value=[routine]), \
                patch.object(self.w, "notify_alert") as notify, contextlib.redirect_stdout(io.StringIO()) as output:
            self.w.run_daily(False)
        notify.assert_not_called()
        self.assertIn("0/1 enabled", output.getvalue())
        self.assertNotIn("cf=9", output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
