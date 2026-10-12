import ast
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import types
import unittest
from unittest import mock


source = ast.parse(Path(__file__).with_name("kit_compat_launcher.py").read_text())
selected = [node for node in source.body if
            isinstance(node, ast.FunctionDef) and node.name in
            {"_safe_diagnostic", "_relay_diagnostic_line", "_drain_child_diagnostics",
             "_relay_child_diagnostics", "_watch_child"} or
            isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "_DIAGNOSTIC_STAGES"
                for target in node.targets)]
namespace = {"json": json, "sys": sys, "os": os, "time": time, "signal": signal}
exec(compile(ast.Module(body=selected, type_ignores=[]), "safe-diagnostics", "exec"), namespace)


@contextlib.contextmanager
def diagnostic_pipe(payload=b"", *, keep_writer=False):
    read_fd, write_fd = os.pipe()
    stream = os.fdopen(read_fd, "rb", buffering=0)
    try:
        if payload:
            os.write(write_fd, payload)
        if not keep_writer:
            os.close(write_fd)
            write_fd = None
        yield types.SimpleNamespace(stderr=stream)
    finally:
        stream.close()
        if write_fd is not None:
            os.close(write_fd)


class SafeDiagnosticTests(unittest.TestCase):
    def capture(self, callback):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            callback()
        return output.getvalue()

    def test_exception_body_is_never_formatted(self):
        class SecretError(Exception):
            errno = 13
            code = "secret-value"

            def __str__(self):
                raise AssertionError("Exception body must not be read")

        text = self.capture(lambda: namespace["_safe_diagnostic"](SecretError(), "sdk-listen"))
        self.assertEqual(json.loads(text), {"diagnostic": "sdk_subscription", "stage": "sdk-listen",
                                           "exception_type": "SecretError", "errno": 13,
                                           "credential_invalid": False})

    def test_exact_credential_error_becomes_boolean_only(self):
        text = self.capture(lambda: namespace["_safe_diagnostic"](
            RuntimeError("app_id or app_secret is invalid"), "sdk-listen"))
        self.assertTrue(json.loads(text)["credential_invalid"])
        self.assertNotIn("app_id or app_secret is invalid", text)

    def test_original_cause_retains_only_numeric_http_status(self):
        inner = OSError("credential-sentinel")
        inner.response = types.SimpleNamespace(status_code=403, text="private-body")
        outer = RuntimeError("private-wrapper")
        outer.__cause__ = inner
        text = self.capture(lambda: namespace["_safe_diagnostic"](outer, "sdk-listen"))
        self.assertEqual(json.loads(text)["status_code"], 403)
        self.assertNotIn("credential-sentinel", text)
        self.assertNotIn("private-body", text)

    def test_child_raw_output_and_extra_fields_are_discarded(self):
        payload = b'Authorization: credential-sentinel\n' + json.dumps({
            "diagnostic": "sdk_subscription", "stage": "sdk-listen", "exception_type": "HTTPError",
            "status_code": 403, "body": "private-body", "headers": "private-header",
        }).encode() + b'\n'
        with diagnostic_pipe(payload) as proc:
            text = self.capture(lambda: namespace["_relay_child_diagnostics"](proc))
        self.assertEqual(json.loads(text), {"diagnostic": "sdk_subscription", "stage": "sdk-listen",
                                           "exception_type": "HTTPError", "status_code": 403})

    def test_untrusted_stage_and_exception_names_are_discarded(self):
        payload = b'{"diagnostic":"sdk_subscription","stage":"secret-stage","exception_type":"HTTPError"}\n'
        payload += b'{"diagnostic":"sdk_subscription","stage":"sdk-listen","exception_type":"unsafe name"}\n'
        with diagnostic_pipe(payload) as proc:
            self.assertEqual(self.capture(lambda: namespace["_relay_child_diagnostics"](proc)), "")

    def test_live_empty_pipe_does_not_wait_for_writer(self):
        with diagnostic_pipe(keep_writer=True) as proc:
            state = {"partial": b"", "discarding": False, "eof": False}
            self.assertEqual(self.capture(lambda: namespace["_relay_child_diagnostics"](
                proc, state, final=False)), "")
            self.assertFalse(state["eof"])
            self.assertFalse(proc.stderr.closed)

    def test_cleanup_has_deadline_when_write_end_remains_open(self):
        ticks = iter((0.0, 0.0, 0.1, 0.6))
        with diagnostic_pipe(keep_writer=True) as proc:
            self.assertEqual(self.capture(lambda: namespace["_relay_child_diagnostics"](
                proc, clock=lambda: next(ticks), pause=lambda _seconds: None)), "")
            self.assertTrue(proc.stderr.closed)

    def test_monitor_drains_more_than_pipe_capacity_and_filters_long_line(self):
        clean = {"diagnostic": "sdk_subscription", "stage": "sdk-listen",
                 "exception_type": "HTTPError", "status_code": 403}
        payload = json.dumps({**clean, "body": "private-body"}).encode() + b"\n"
        code = "import os; os.write(2, b'x' * 131072 + b'\\n' + " + repr(payload) + ")"
        proc = subprocess.Popen([sys.executable, "-c", code], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        done, failed = threading.Event(), threading.Event()
        state = {"partial": b"", "discarding": False, "eof": False}
        monitor = threading.Thread(target=namespace["_watch_child"],
                                   args=(proc, done, failed, os.getpid(), state))
        output = io.StringIO()
        try:
            with mock.patch.object(os, "kill") as parent_signal, contextlib.redirect_stderr(output):
                monitor.start()
                proc.wait(timeout=4)
                monitor.join(timeout=1)
                self.assertFalse(monitor.is_alive())
                self.assertTrue(failed.is_set())
                parent_signal.assert_called_once_with(os.getpid(), signal.SIGUSR1)
                namespace["_relay_child_diagnostics"](proc, state)
            self.assertEqual(json.loads(output.getvalue()), clean)
            self.assertLessEqual(len(state["partial"]), 4096)
            self.assertNotIn("private-body", output.getvalue())
        finally:
            done.set()
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=1)
            monitor.join(timeout=1)
            proc.stderr.close()


if __name__ == "__main__":
    unittest.main()
