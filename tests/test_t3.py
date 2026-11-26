"""Exercise the T3 transport with local executables, without a provider login."""

from __future__ import annotations

from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from controlmesh import t3


class T3TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ)
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop("CONTROL_MESH_T3_BINARY", None)

    def executable(self, path, source):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"#!{sys.executable}\n{source}\n", encoding="utf-8")
        path.chmod(0o700)
        return path

    def local_runtime(self, source="print('T3 runtime')"):
        return self.executable(self.root / "node_modules" / ".bin" / "t3", source)

    def test_checkout_runtime_is_selected_without_path_lookup(self):
        local = self.local_runtime()
        os.environ["PATH"] = str(self.root / "unrelated-global-bin")
        self.assertEqual(t3.resolve_t3_binary(repository_root=self.root), local)
        result = t3.run_t3(["--version"], repository_root=self.root, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "T3 runtime\n")

    def test_explicit_binary_wins_over_environment(self):
        selected = self.executable(self.root / "t3 with spaces", "print('explicit')")
        os.environ["CONTROL_MESH_T3_BINARY"] = str(self.root / "missing")
        self.assertEqual(t3.resolve_t3_binary(selected), selected)

    def test_environment_override_supports_installed_wheel(self):
        selected = self.executable(self.root / "runtime" / "t3", "print('selected')")
        os.environ["CONTROL_MESH_T3_BINARY"] = str(selected)
        result = t3.run_t3(["--version"], repository_root=self.root, capture_output=True)
        self.assertEqual(result.stdout, "selected\n")

    def test_missing_local_runtime_does_not_fall_back_to_global_binary(self):
        self.executable(self.root / "global" / "t3", "print('wrong release')")
        os.environ["PATH"] = str(self.root / "global")
        with self.assertRaisesRegex(t3.T3BinaryNotFound, "npm ci"):
            t3.resolve_t3_binary(repository_root=self.root)

    def test_argument_and_stdin_boundaries_are_preserved(self):
        executable = self.local_runtime(
            "import json, os, sys\n"
            "print(json.dumps({'args': sys.argv[1:], 'stdin': sys.stdin.read(), "
            "'cwd': os.getcwd()}))"
        )
        marker = self.root / "must-not-exist"
        arguments = [
            "thread", "start", "project with spaces", "-", "--title",
            f"$(touch {marker}); `touch {marker}`", "--wait", "--json",
        ]
        prompt = "保留换行\nUse $HOME literally; `echo nope`; $(echo nope)"
        result = t3.run_t3(
            arguments, binary=executable, cwd=self.root, input_text=prompt, capture_output=True
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload, {"args": arguments, "stdin": prompt, "cwd": str(self.root)})
        self.assertFalse(marker.exists())

    def test_waiting_json_and_exit_two_are_not_rewritten(self):
        payload = {"threadId": "thread-1", "runId": "run-1", "status": "waiting",
                   "reply": None, "error": None}
        output = json.dumps(payload)
        runtime = self.local_runtime(
            f"import sys\nprint({output!r})\n"
            "print('Thread thread-1 is waiting for an answer.', file=sys.stderr)\n"
            "sys.exit(2)"
        )
        os.environ["CONTROL_MESH_T3_BINARY"] = str(runtime)
        result = subprocess.run(
            [sys.executable, "-B", "-S", "-m", "controlmesh.t3",
             "thread", "send", "thread-1", "-", "--wait", "--json"],
            input="Continue after the supplied answer.",
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, output + "\n")
        self.assertEqual(result.stderr, "Thread thread-1 is waiting for an answer.\n")

    def test_usage_error_is_not_relabelled_as_waiting(self):
        runtime = self.local_runtime(
            "import sys\nprint('Unknown option --bad', file=sys.stderr)\nsys.exit(2)"
        )
        result = t3.run_t3(["--bad"], binary=runtime, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "Unknown option --bad\n")

    def test_timeout_does_not_retry_or_send_a_stop_command(self):
        launches = self.root / "launches"
        runtime = self.local_runtime(
            "import time\nfrom pathlib import Path\n"
            f"with Path({str(launches)!r}).open('a') as log:\n"
            "    log.write('started\\n')\n"
            "time.sleep(10)"
        )
        with self.assertRaises(subprocess.TimeoutExpired):
            t3.run_t3(["thread", "show", "thread-1"], binary=runtime,
                      capture_output=True, timeout=0.2)
        self.assertEqual(launches.read_text(), "started\n")

    def test_missing_binary_returns_actionable_cli_error(self):
        os.environ["CONTROL_MESH_T3_BINARY"] = str(self.root / "missing")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = t3.main(["--version"])
        self.assertEqual(code, 127)
        self.assertIn("CONTROL_MESH_T3_BINARY", stderr.getvalue())

    def test_non_executable_runtime_is_reported(self):
        runtime = self.local_runtime()
        runtime.chmod(0o600)
        os.environ["CONTROL_MESH_T3_BINARY"] = str(runtime)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(t3.main(["--version"]), 126)

    @unittest.skipUnless(os.name == "posix", "POSIX signal status")
    def test_native_signal_exit_is_not_converted_to_an_unsigned_exit_code(self):
        runtime = self.local_runtime("import os, signal\nos.kill(os.getpid(), signal.SIGTERM)")
        os.environ["CONTROL_MESH_T3_BINARY"] = str(runtime)
        result = subprocess.run(
            [sys.executable, "-B", "-S", "-m", "controlmesh.t3", "serve"],
            text=True, capture_output=True, timeout=5, check=False,
        )
        self.assertEqual(result.returncode, -signal.SIGTERM)

    @unittest.skipUnless(os.name == "posix", "POSIX process replacement")
    def test_targeted_termination_reaches_the_runtime_without_an_orphan_wrapper(self):
        pidfile = self.root / "runtime.pid"
        runtime = self.local_runtime(
            "import os, time\nfrom pathlib import Path\n"
            f"Path({str(pidfile)!r}).write_text(str(os.getpid()))\ntime.sleep(30)"
        )
        os.environ["CONTROL_MESH_T3_BINARY"] = str(runtime)
        process = subprocess.Popen(
            [sys.executable, "-B", "-S", "-m", "controlmesh.t3", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        runtime_pid = None
        try:
            deadline = time.monotonic() + 3
            while not pidfile.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            runtime_pid = int(pidfile.read_text())
            self.assertEqual(runtime_pid, process.pid)
            process.terminate()
            self.assertEqual(process.wait(timeout=3), -signal.SIGTERM)
            with self.assertRaises(ProcessLookupError):
                os.kill(runtime_pid, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            if runtime_pid and runtime_pid != process.pid:
                try:
                    os.kill(runtime_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_interrupt_before_process_replacement_returns_130(self):
        with patch.object(t3, "resolve_t3_binary", side_effect=KeyboardInterrupt):
            self.assertEqual(t3.main(["--version"]), 130)


if __name__ == "__main__":
    unittest.main()
