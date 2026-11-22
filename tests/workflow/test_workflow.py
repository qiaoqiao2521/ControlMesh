"""Thin CLI routing plus opt-in real SpecMesh handoff/consumption checks."""

# ruff: noqa: INP001, PT009, PT027
# Keep this entry-point contract suite runnable with the standard library alone.

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from controlmesh import workflow


REPO = Path(__file__).resolve().parents[2]
HEAD = "a" * 40
TASK = "plans/small-change"


class WorkflowAdapterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.specmesh = self.root / "trusted-specmesh"
        (self.specmesh / "specmesh_port").mkdir(parents=True)
        (self.specmesh / "specmesh_port/__main__.py").write_text("", encoding="utf-8")

    def arguments(self, operation="prepare"):
        args = [operation, "--repo", str(self.project), "--task", TASK,
                "--specmesh-root", str(self.specmesh), "--scope", "src/example.py"]
        return args + (["--expected-head", HEAD] if operation == "prepare" else ["--handoff", "packet.json"])

    def prepared(self):
        # Only the adapter's framing fields are needed by this process double;
        # upstream schema/extraction behavior is exercised by the native tests.
        return {"schema_version": "specmesh.handoff.v1", "state": "ready", "executable": True,
                "task": {"path": TASK}, "baseline": {"observed_head": HEAD, "expected_head": HEAD},
                "issues": [], "upstream_text": "保留原文与顺序"}

    def invoke(self, args, value, *, returncode=0):
        stdout = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, indent=2).encode() + b"\n"
        result = subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=b"")
        output, error = io.StringIO(), io.StringIO()
        with patch.object(workflow.subprocess, "run", return_value=result) as run, \
                redirect_stdout(output), redirect_stderr(error):
            code = workflow.main(args)
        return code, output.getvalue(), error.getvalue(), run

    def test_prepare_selects_native_handoff_and_preserves_json(self):
        raw = json.dumps(self.prepared(), ensure_ascii=False, indent=3).encode() + b"\n\n"
        with patch.dict(os.environ, {"SYNTHETIC_PROVIDER_KEY": "must-not-pass", "PYTHONPATH": "/ignored"}):
            code, output, error, run = self.invoke(self.arguments(), raw)
        self.assertEqual(code, 0, error)
        self.assertEqual(output.encode(), raw)
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--handoff") + 1], "json")
        self.assertEqual(argv[argv.index("--scope-path") + 1], "src/example.py")
        self.assertTrue({"-B", "-S", "-E"}.issubset(argv))
        self.assertEqual(run.call_args.kwargs["cwd"], self.specmesh)
        self.assertNotIn("SYNTHETIC_PROVIDER_KEY", run.call_args.kwargs["env"])
        self.assertNotIn("PYTHONPATH", run.call_args.kwargs["env"])
        request = json.loads(run.call_args.kwargs["input"])
        self.assertEqual(request["operation"], "prepare_handoff")
        self.assertEqual(request["task_path"], TASK)
        self.assertEqual(request["expected_head"], HEAD)
        self.assertFalse((self.project / ".controlmesh").exists())
        # Preserve bytes even if the invoking host's text encoding or newline
        # configuration differs from SpecMesh's UTF-8 output.
        captured = io.BytesIO()
        text_stream = io.TextIOWrapper(captured, encoding="ascii", newline="\r\n")
        result = subprocess.CompletedProcess([], 0, stdout=raw, stderr=b"")
        with patch.object(workflow.subprocess, "run", return_value=result), \
                redirect_stdout(text_stream), redirect_stderr(io.StringIO()):
            self.assertEqual(workflow.main(self.arguments()), 0)
        self.assertEqual(captured.getvalue(), raw)
        text_stream.detach()

    def test_check_passes_independent_scope_without_reading_packet(self):
        result = {"schema_version": "specmesh.handoff.v1", "state": "ready", "executable": True,
                  "verified": True, "issues": []}
        args = [*self.arguments("check"), "--scope", "tests/example.py"]
        code, output, error, run = self.invoke(args, result)
        self.assertEqual(code, 0, error)
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--verify-handoff") + 1], str(Path.cwd() / "packet.json"))
        self.assertEqual(argv[argv.index("--task-path") + 1], TASK)
        self.assertEqual([argv[n + 1] for n, arg in enumerate(argv) if arg == "--scope-path"],
                         ["src/example.py", "tests/example.py"])
        self.assertEqual(run.call_args.kwargs["input"], b"")
        self.assertEqual(json.loads(output), result)

    def test_old_empty_malformed_and_wrong_interfaces_are_rejected(self):
        bad = [b"", b"not-json", b"{}", b"[]", b'{"status":"pass"}',
               b'{"schema_version":"specmesh.handoff.v1","state":"ready","executable":true,"issues":[]}',
               json.dumps(dict(self.prepared(), executable="true")).encode()]
        for raw in bad:
            with self.subTest(response=raw):
                code, output, error, _ = self.invoke(self.arguments(), raw)
                self.assertEqual(code, 2)
                self.assertEqual(output, "")
                self.assertIn("workflow_request_failed", error)
        code, output, _, _ = self.invoke(self.arguments("check"), self.prepared())
        self.assertEqual(code, 2)
        self.assertEqual(output, "")

    def test_nonzero_or_nonexecutable_never_becomes_success(self):
        code, output, _, _ = self.invoke(self.arguments(), self.prepared(), returncode=7)
        self.assertEqual(code, 7)
        self.assertEqual(json.loads(output), self.prepared())
        blocked = dict(self.prepared(), executable=False, state="blocked")
        code, output, _, _ = self.invoke(self.arguments(), blocked)
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(output), blocked)
        forged = dict(self.prepared(), task={"path": "plans/other"})
        self.assertEqual(self.invoke(self.arguments(), forged)[0], 2)

    def test_timeout_and_missing_trusted_checkout_fail_without_runtime_fallback(self):
        output, error = io.StringIO(), io.StringIO()
        with patch.object(workflow.subprocess, "run", side_effect=subprocess.TimeoutExpired("specmesh", 1)) as run, \
                redirect_stdout(output), redirect_stderr(error):
            self.assertEqual(workflow.main(self.arguments()), 2)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("specmesh_timeout", error.getvalue())
        args = self.arguments()
        args[args.index("--specmesh-root") + 1] = str(self.root / "absent")
        code, _, _, run = self.invoke(args, self.prepared())
        self.assertEqual(code, 2)
        run.assert_not_called()

    def test_invalid_timeout_paths_and_missing_selection_reject_before_subprocess(self):
        variants = [[*self.arguments(), "--timeout", value] for value in ("0", "-1", "61", "nan", "inf")]
        for path in ("../escape", "/absolute", ".git/config"):
            args = self.arguments()
            args[args.index("--task") + 1] = path
            variants.append(args)
        args = self.arguments("check")
        position = args.index("--task")
        del args[position:position + 2]
        variants.append(args)
        for args in variants:
            with self.subTest(args=args), patch.object(workflow.subprocess, "run") as run, \
                    redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                workflow.main(args)
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called()


class NativeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("CM_SPECMESH_TEST_ROOT")
        if configured is None:
            raise unittest.SkipTest("CM_SPECMESH_TEST_ROOT is not configured")
        if not configured or not (Path(configured).expanduser() / "specmesh_port/__main__.py").is_file():
            raise AssertionError("CM_SPECMESH_TEST_ROOT must identify a real independent SpecMesh checkout")
        cls.specmesh = Path(configured).expanduser().resolve(strict=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.project = self.directory / "project"
        self.project.mkdir()
        self.task = self.project / TASK
        self.task.mkdir(parents=True)
        (self.project / "AGENTS.md").write_text("# Instructions\nUse focused deterministic checks.\n", encoding="utf-8")
        (self.project / "PROJECT.md").write_text(
            "# Small change\n\n## Why\nDeliver one bounded change.\n\n## Constraints\n"
            "Keep ordinary files. No runtime or services.\n", encoding="utf-8")
        (self.task / "task_plan.md").write_text(
            "# Small change\n\n## Goal\nThe delivered number must equal four.\n\n"
            "## Status\nin progress\n\n## Next\nIndependently check the selected result.\n", encoding="utf-8")
        (self.task / "findings.md").write_text(
            "# Findings\n\n## Evidence\n- [Worker declaration](verification.txt)\n", encoding="utf-8")
        (self.task / "progress.md").write_text(
            "# Progress\n\n## Current\nin progress\n\n## Done\n- Worker reported completion.\n", encoding="utf-8")
        (self.task / "verification.txt").write_text("Result: passed\nreviewer: synthetic worker\n", encoding="utf-8")
        (self.project / "result.txt").write_text("3\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("config", "user.name", "Workflow Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("add", ".")
        self.git("commit", "-qm", "Synthetic baseline")
        self.head = self.git("rev-parse", "HEAD")
        self.packet = self.directory / "handoff.json"

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.project), *args], text=True).strip()

    def invoke(self, operation, *, head=None, handoff=None, scope=("result.txt",), input_data=None):
        args = [sys.executable, "-B", "-S", "-E", "-m", "controlmesh.workflow", operation,
                "--repo", str(self.project), "--task", TASK, "--specmesh-root", str(self.specmesh),
                "--timeout", "10"]
        for path in scope:
            args += ["--scope", path]
        args += (["--expected-head", head or self.head] if operation == "prepare" else
                 ["--handoff", str(self.packet) if handoff is None else str(handoff)])
        return subprocess.run(args, cwd=REPO, input=input_data, capture_output=True, timeout=15, check=False)

    def prepare(self, *, head=None):
        result = self.invoke("prepare", head=head)
        self.assertEqual(result.returncode, 0, result.stderr.decode() + result.stdout.decode())
        self.packet.write_bytes(result.stdout)
        return json.loads(result.stdout)

    def test_real_prepare_and_new_process_check_preserve_upstream_contract(self):
        before = self.git("status", "--porcelain")
        packet = self.prepare()
        # prepare has exited; a fresh process consumes only the saved file plus
        # its independently supplied task/scope. There is no adapter state.
        checked = self.invoke("check")
        self.assertEqual(checked.returncode, 0, checked.stderr.decode() + checked.stdout.decode())
        self.assertTrue(json.loads(checked.stdout)["verified"])
        self.assertEqual(packet["task"]["path"], TASK)
        self.assertIn("result.txt", packet["dirty_coverage"]["scope"]["selected_paths"])
        self.assertEqual(self.git("status", "--porcelain"), before)
        self.assertFalse((self.project / ".controlmesh").exists())
        from_stdin = self.invoke("check", handoff="-", input_data=self.packet.read_bytes())
        self.assertEqual(from_stdin.returncode, 0, from_stdin.stderr.decode())

    def test_selected_bytes_and_head_expire_then_fresh_prepare_can_continue(self):
        self.prepare()
        (self.project / "result.txt").write_text("4\n", encoding="utf-8")
        stale_bytes = self.invoke("check")
        self.assertNotEqual(stale_bytes.returncode, 0)
        self.assertFalse(json.loads(stale_bytes.stdout)["verified"])
        self.prepare()
        self.assertEqual(self.invoke("check").returncode, 0)
        self.git("add", "result.txt")
        self.git("commit", "-qm", "Correct the selected result")
        stale_head = self.invoke("check")
        self.assertNotEqual(stale_head.returncode, 0)
        self.assertFalse(json.loads(stale_head.stdout)["verified"])
        self.assertNotEqual(self.invoke("prepare").returncode, 0)
        self.prepare(head=self.git("rev-parse", "HEAD"))
        self.assertEqual(self.invoke("check").returncode, 0)

    def test_packet_scope_is_not_adopted_and_symlink_is_not_resolved(self):
        self.prepare()
        omitted = self.invoke("check", scope=())
        self.assertNotEqual(omitted.returncode, 0)
        self.assertFalse(json.loads(omitted.stdout)["verified"])
        link = self.directory / "linked-handoff.json"
        link.symlink_to(self.packet)
        rejected = self.invoke("check", handoff=link)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(rejected.stdout, b"")

    def test_consumable_self_report_is_not_business_correctness(self):
        packet = self.prepare()
        self.assertTrue(packet["executable"])
        self.assertEqual(self.invoke("check").returncode, 0)
        self.assertEqual(packet["work_summary"]["completed"][0]["authority"], "asserted_candidate")
        self.assertTrue(all(not row["is_external"] for row in packet["evidence_bindings"]))
        # A factual independent assertion still rejects the worker's claim.
        self.assertNotEqual(int((self.project / "result.txt").read_text()), 4)
        self.assertNotIn("business_accepted", packet)


if __name__ == "__main__":
    unittest.main()
