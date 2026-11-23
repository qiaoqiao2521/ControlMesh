"""Real subprocess checks for the dependency-free execution CLI."""

from __future__ import annotations

import contextlib
import ctypes
import io
import json
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(sys.platform.startswith("linux"), "owned process cleanup currently requires Linux")
class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.cwd = Path(self.temporary.name)
        self.task = self.cwd / "task.md"
        self.task.write_text("Produce result.txt containing 4.\n")
        self.writer = self.cwd / "write.py"
        self.writer.write_text("from pathlib import Path\nPath('result.txt').write_text('4')\n")
        self.checker = self.cwd / "check.py"
        self.checker.write_text("from pathlib import Path\nassert Path('result.txt').read_text() == '4'\n")

    def argv(self, *, report="report.json", verify=True, artifact=True, command=None, extra=()):
        arguments = [
            sys.executable, "-B", "-S", "-m", "controlmesh.execution",
            "--cwd", str(self.cwd), "--task", "task.md", "--report", report,
        ]
        if verify:
            arguments += ["--verify", shlex.join([sys.executable, "check.py"])]
        if artifact:
            arguments += ["--artifact", "result.txt"]
        arguments += list(extra)
        arguments += ["--", *(command or [sys.executable, "write.py"])]
        return arguments

    def run_cm(self, **kwargs):
        result = subprocess.run(self.argv(**kwargs), cwd=ROOT, capture_output=True, text=True, timeout=15)
        report = self.cwd / kwargs.get("report", "report.json")
        try:
            value = json.loads(report.read_text()) if report.is_file() else None
        except json.JSONDecodeError:
            value = None  # The destination may be an existing protected input.
        return result, value

    def test_success_and_private_replayable_logs(self):
        self.writer.write_text("from pathlib import Path\nprint('written')\nPath('result.txt').write_text('4')\n")
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["next_action"], "deliver")
        self.assertEqual(report["execution"]["exit_code"], 0)
        self.assertTrue(report["artifacts"][0]["sha256"])
        self.assertEqual(report["identity"]["task"]["path"], "task.md")
        self.assertTrue(report["advisory"])
        log = self.cwd / report["execution"]["stdout_log"]
        self.assertEqual(log.read_text(), "written\n")
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)
        self.assertEqual(log.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.cwd / "report.json").stat().st_mode & 0o777, 0o600)

    def test_exit_zero_does_not_override_failed_verification(self):
        self.writer.write_text("from pathlib import Path\nPath('result.txt').write_text('3')\n")
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["execution"]["exit_code"], 0)
        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(report["next_action"], "repair")
        self.assertEqual(report["verification"][0]["state"], "failed")

    def test_nonzero_execution_does_not_become_success(self):
        self.writer.write_text("from pathlib import Path\nPath('result.txt').write_text('4')\nraise SystemExit(7)\n")
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(report["execution"]["exit_code"], 7)
        self.assertEqual(report["verification"][0]["exit_code"], 0)

    def test_missing_required_artifact_fails_successful_command(self):
        self.writer.write_text("pass\n")
        self.checker.write_text("pass\n")
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(report["artifacts"][0]["error"], "missing")

    def test_artifact_existence_is_not_business_verification(self):
        result, report = self.run_cm(verify=False)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["status"], "unverified")
        self.assertEqual(report["next_action"], "verify")

    def test_missing_executor_suggests_host_fallback(self):
        result, report = self.run_cm(command=[str(self.cwd / "missing-command")])
        self.assertEqual(result.returncode, 4)
        self.assertEqual(report["status"], "tool_unavailable")
        self.assertEqual(report["next_action"], "use_host_agent")
        self.assertEqual(report["verification"], [])

    def test_missing_verifier_is_unverified(self):
        result, report = self.run_cm(verify=False, extra=["--verify", "nonexistent-cm-test-verifier"])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["status"], "unverified")
        self.assertEqual(report["verification"][0]["state"], "unavailable")

    def test_unchanged_failure_suggests_different_approach_without_retry(self):
        self.writer.write_text(
            "from pathlib import Path\n"
            "p=Path('calls.txt')\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
            "Path('result.txt').write_text('3')\n"
        )
        first, before = self.run_cm(report="first.json")
        second, after = self.run_cm(report="second.json", extra=["--previous-report", "first.json"])
        self.assertEqual((first.returncode, second.returncode), (1, 1))
        self.assertEqual(after["next_action"], "change_approach")
        self.assertEqual(after["comparison"]["evidence_changed"], False)
        self.assertEqual(before["evidence_fingerprint"], after["evidence_fingerprint"])
        self.assertEqual((self.cwd / "calls.txt").read_text(), "2")

    def test_changed_result_can_complete_after_previous_failure(self):
        self.writer.write_text("from pathlib import Path\nPath('result.txt').write_text('3')\n")
        self.run_cm(report="first.json")
        self.writer.write_text("from pathlib import Path\nPath('result.txt').write_text('4')\n")
        result, report = self.run_cm(report="second.json", extra=["--previous-report", "first.json"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["next_action"], "deliver")
        self.assertEqual(report["comparison"]["evidence_changed"], True)

    def test_other_task_or_contract_previous_report_rejected_before_execution(self):
        self.run_cm(report="first.json")
        (self.cwd / "result.txt").unlink()
        self.task.write_text("A different task\n")
        result, report = self.run_cm(report="second.json", extra=["--previous-report", "first.json"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertFalse((self.cwd / "result.txt").exists())
        self.assertIn("does not match", result.stderr)

    def test_different_cwd_previous_report_rejected(self):
        self.run_cm(report="first.json")
        original = self.cwd
        self.cwd = original / "other"
        self.cwd.mkdir()
        (self.cwd / "task.md").write_bytes(self.task.read_bytes())
        result, report = self.run_cm(extra=["--previous-report", str(original / "first.json")])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)

    def test_invalid_previous_report_rejected_before_execution(self):
        (self.cwd / "bad.json").write_text('{"schema_version":"wrong"}')
        result, report = self.run_cm(extra=["--previous-report", "bad.json"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertFalse((self.cwd / "result.txt").exists())

    def test_existing_report_or_input_is_never_overwritten(self):
        original = self.task.read_bytes()
        result, _ = self.run_cm(report="task.md")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.task.read_bytes(), original)
        self.assertFalse((self.cwd / "result.txt").exists())

    def test_report_artifact_overlap_rejected_before_command(self):
        result, report = self.run_cm(report="result.txt")
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertFalse((self.cwd / "result.txt").exists())

    def test_task_is_not_implicitly_executed(self):
        self.task.write_text("touch unauthorized.txt\n")
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.cwd / "unauthorized.txt").exists())
        self.assertEqual(report["execution"]["argv"], [sys.executable, "write.py"])

    def test_shell_syntax_is_literal_in_execution_and_verification(self):
        script = "import sys; assert sys.argv[1] == '; touch unauthorized.txt'"
        result, _ = self.run_cm(
            verify=False, artifact=False,
            command=[sys.executable, "-c", script, "; touch unauthorized.txt"],
            extra=["--verify", shlex.join([sys.executable, "-c", script, "; touch unauthorized.txt"])],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.cwd / "unauthorized.txt").exists())

    def test_output_symlink_is_not_accepted_or_read(self):
        self.writer.write_text("from pathlib import Path\nPath('result.txt').symlink_to('/etc/passwd')\n")
        self.checker.write_text("pass\n")
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(report["artifacts"][0]["exists"])
        self.assertNotIn("sha256", report["artifacts"][0])

    def test_timeout_stops_detached_descendant_before_report(self):
        child = self.cwd / "child.py"
        child.write_text(
            "import signal,time\nfrom pathlib import Path\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "Path('child-ready').write_text('ready')\n"
            "time.sleep(1)\nPath('late-write').write_text('bad')\n"
        )
        self.writer.write_text(
            "import subprocess,sys,time\n"
            "subprocess.Popen([sys.executable, 'child.py'], start_new_session=True)\n"
            "time.sleep(10)\n"
        )
        result, report = self.run_cm(extra=["--timeout", "0.3"])
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertEqual(report["status"], "timed_out")
        self.assertEqual(report["next_action"], "diagnose_timeout")
        self.assertTrue(report["execution"]["cleanup_complete"])
        self.assertTrue((self.cwd / "child-ready").exists())
        time.sleep(1.05)
        self.assertFalse((self.cwd / "late-write").exists())

    def test_term_handler_forked_empty_environment_child_is_stopped(self):
        child = (
            "import signal,time;from pathlib import Path;"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN);"
            "time.sleep(0.6);Path('late-write').write_text('term-child')"
        )
        self.writer.write_text(
            "import os,signal,subprocess,sys,time\nfrom pathlib import Path\n"
            "def on_term(signum, frame):\n"
            f"    child = subprocess.Popen([sys.executable, '-c', {child!r}], start_new_session=True, env={{}})\n"
            "    Path('term-spawned').write_text(str(child.pid))\n"
            "    os._exit(0)\n"
            "signal.signal(signal.SIGTERM, on_term)\ntime.sleep(10)\n"
        )
        result, report = self.run_cm(extra=["--timeout", "0.3"])
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertTrue((self.cwd / "term-spawned").exists())
        self.assertTrue(report["execution"]["cleanup_complete"])
        self.assertEqual(report["execution"]["exit_code"], 0)
        time.sleep(0.8)
        self.assertFalse((self.cwd / "late-write").exists())

    def test_fast_exit_does_not_leave_detached_child_writing(self):
        child = "import time;from pathlib import Path;time.sleep(0.8);Path('late-write').write_text('bad')"
        self.writer.write_text(
            "import subprocess,sys\n"
            f"subprocess.Popen([sys.executable, '-c', {child!r}], start_new_session=True)\n"
        )
        result, report = self.run_cm(verify=False, artifact=False)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertTrue(report["execution"]["cleanup_complete"])
        time.sleep(0.85)
        self.assertFalse((self.cwd / "late-write").exists())

    def test_sanitized_environment_orphan_cannot_change_accepted_artifact(self):
        child = "import time;from pathlib import Path;time.sleep(0.6);Path('result.txt').write_text('late-child-write')"
        self.writer.write_text(
            "from pathlib import Path\nimport subprocess,sys\n"
            "Path('result.txt').write_text('4')\n"
            f"subprocess.Popen([sys.executable, '-c', {child!r}], start_new_session=True, env={{}})\n"
        )
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "completed")
        self.assertTrue(report["execution"]["cleanup_complete"])
        time.sleep(0.8)
        self.assertEqual((self.cwd / "result.txt").read_text(), "4")

    def test_double_forked_empty_environment_descendant_is_stopped(self):
        middle = self.cwd / "middle.py"
        middle.write_text(
            "import os,time\nfrom pathlib import Path\n"
            "if os.fork(): os._exit(0)\n"
            "os.setsid()\n"
            "if os.fork(): os._exit(0)\n"
            "Path('orphan-ready').write_text('yes')\n"
            "time.sleep(0.6)\nPath('result.txt').write_text('late-double-fork')\n"
        )
        self.writer.write_text(
            "from pathlib import Path\nimport subprocess,sys,time\n"
            "Path('result.txt').write_text('4')\n"
            "subprocess.Popen([sys.executable, 'middle.py'], start_new_session=True, env={})\n"
            "while not Path('orphan-ready').exists(): time.sleep(0.01)\n"
        )
        result, report = self.run_cm()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.cwd / "orphan-ready").exists())
        self.assertTrue(report["execution"]["cleanup_complete"])
        time.sleep(0.8)
        self.assertEqual((self.cwd / "result.txt").read_text(), "4")

    def test_host_unrelated_child_survives_owned_cleanup(self):
        from controlmesh.execution import main

        unrelated = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(10)"])
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(self.argv()[5:]), 0)
            self.assertIsNone(unrelated.poll())
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=3)

    def test_supervisor_failure_never_claims_cleanup_complete(self):
        self.writer.write_text("import os,signal\nos.kill(os.getppid(), signal.SIGKILL)\n")
        result, report = self.run_cm(verify=False, artifact=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(report["next_action"], "diagnose_cleanup")
        self.assertFalse(report["execution"]["cleanup_complete"])

    def test_total_timeout_also_bounds_verification(self):
        self.writer.write_text("import time\nfrom pathlib import Path\ntime.sleep(0.2)\nPath('result.txt').write_text('4')\n")
        self.checker.write_text("import time\ntime.sleep(1)\n")
        result, report = self.run_cm(extra=["--timeout", "0.4"])
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertEqual(report["execution"]["state"], "succeeded")
        self.assertEqual(report["verification"][0]["state"], "timed_out")

    def test_sigterm_records_interruption_and_stops_children(self):
        self.writer.write_text(
            "from pathlib import Path\nimport time\n"
            "Path('ready').write_text('yes')\ntime.sleep(1)\nPath('late-write').write_text('bad')\n"
        )
        proc = subprocess.Popen(self.argv(), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: proc.kill() if proc.poll() is None else None)
        deadline = time.monotonic() + 3
        while not (self.cwd / "ready").exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue((self.cwd / "ready").exists())
        proc.send_signal(signal.SIGTERM)
        _, stderr = proc.communicate(timeout=5)
        report = json.loads((self.cwd / "report.json").read_text())
        self.assertEqual(proc.returncode, 143, stderr)
        self.assertEqual(report["status"], "interrupted")
        self.assertTrue(report["execution"]["cleanup_complete"])
        time.sleep(1.05)
        self.assertFalse((self.cwd / "late-write").exists())

    def test_call_restores_callers_subreaper_and_signal_handlers(self):
        from controlmesh.execution import main

        libc = ctypes.CDLL(None, use_errno=True)
        before = ctypes.c_int()
        after = ctypes.c_int()
        self.assertEqual(libc.prctl(37, ctypes.byref(before), 0, 0, 0), 0)
        handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
        with contextlib.redirect_stdout(io.StringIO()):
            code = main(self.argv()[5:])
        self.assertEqual(code, 0)
        self.assertEqual(libc.prctl(37, ctypes.byref(after), 0, 0, 0), 0)
        self.assertEqual(after.value, before.value)
        self.assertEqual({sig: signal.getsignal(sig) for sig in handlers}, handlers)

    def test_repeated_cleanup_failure_retains_specific_diagnostic(self):
        from unittest.mock import patch

        from controlmesh.execution import main

        outcome = {"argv": [sys.executable, "write.py"], "state": "succeeded", "exit_code": 0, "cleanup_complete": False}
        with patch("controlmesh.execution._run", return_value=outcome), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(self.argv(report="first.json")[5:]), 1)
            self.assertEqual(main(self.argv(report="second.json", extra=["--previous-report", "first.json"])[5:]), 1)
        report = json.loads((self.cwd / "second.json").read_text())
        self.assertFalse(report["comparison"]["evidence_changed"])
        self.assertEqual(report["next_action"], "diagnose_cleanup")


if __name__ == "__main__":
    unittest.main()
