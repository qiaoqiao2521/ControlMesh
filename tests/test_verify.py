"""Exercise real checks and local Git remotes; never invoke a model or push remotely."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from controlmesh import verify


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform.startswith("linux"), "verification process cleanup requires Linux")
class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.cwd = self.base / "project"
        self.cwd.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "CM verification test")
        self.git("config", "user.email", "verify@example.invalid")
        (self.cwd / "result.txt").write_text("4")
        (self.cwd / "check.py").write_text("from pathlib import Path\nassert Path('result.txt').read_text() == '4'\n")
        self.git("add", ".")
        self.git("commit", "-m", "Initial task result")
        self.head = self.git("rev-parse", "HEAD").stdout.strip()

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(
            ["git", *args], cwd=cwd or self.cwd, capture_output=True, text=True,
            check=check, timeout=10,
        )

    def run_verify(self, *, report="report.json", checks=None, artifacts=("result.txt",), extra=(), cwd=None):
        report_path = self.base / report
        argv = [
            sys.executable, "-B", "-S", "-m", "controlmesh.verify", "--cwd", str(cwd or self.cwd),
            "--report", str(report_path),
        ]
        for command in checks if checks is not None else [[sys.executable, "-B", "check.py"]]:
            argv += ["--verify", shlex.join(command)]
        for artifact in artifacts:
            argv += ["--artifact", artifact]
        argv += extra
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=15)
        report_value = json.loads(report_path.read_text()) if report_path.exists() else None
        return result, report_value

    def remote(self):
        remote = self.base / "remote.git"
        self.git("init", "--bare", str(remote))
        self.git("remote", "add", "origin", str(remote))
        return remote

    def test_checks_existing_output_without_execution_stage(self):
        result, report = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "verified")
        self.assertNotIn("execution", report)
        self.assertEqual(len(report["verification"]), 1)
        self.assertEqual(report["source"]["after"]["head"], self.head)
        self.assertTrue(report["source"]["unchanged_during_verification"])
        self.assertFalse(report["delivery"]["requested"])
        self.assertEqual((self.base / "report.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.base / report["logs_directory"]).stat().st_mode & 0o777, 0o700)

    def test_real_failed_check_does_not_become_verified(self):
        (self.cwd / "result.txt").write_text("3")
        result, report = self.run_verify()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(report["verification"][0]["state"], "failed")

    def test_artifact_existence_without_a_check_is_unverified(self):
        result, report = self.run_verify(checks=[])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["status"], "unverified")

    def test_missing_verifier_and_missing_artifact_are_distinguished(self):
        result, report = self.run_verify(checks=[["missing-cm-verifier-123"]])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["verification"][0]["state"], "unavailable")
        result, report = self.run_verify(report="missing.json", artifacts=("missing.bin",))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(report["artifacts"][0]["exists"])

    def test_dirty_tracked_source_is_bound_and_can_pass(self):
        (self.cwd / "check.py").write_text("from pathlib import Path\nassert int(Path('result.txt').read_text()) == 4\n")
        result, report = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report["source"]["after"]["dirty"])
        self.assertTrue(report["source"]["unchanged_during_verification"])

    def test_source_mutation_during_checks_is_not_a_fresh_pass(self):
        command = [sys.executable, "-c", "from pathlib import Path; Path('check.py').write_text('pass\\n')"]
        result, report = self.run_verify(checks=[command])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(report["verification"][0]["state"], "succeeded")
        self.assertFalse(report["source"]["unchanged_during_verification"])
        self.assertEqual(report["next_action"], "verify_current_source")

    def test_untracked_content_change_is_detected_without_status_change(self):
        (self.cwd / "new-module.txt").write_text("before")
        command = [sys.executable, "-c", "from pathlib import Path; Path('new-module.txt').write_text('after')"]
        result, report = self.run_verify(checks=[command])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["source"]["before"]["untracked_count"], 1)
        self.assertEqual(report["source"]["after"]["untracked_count"], 1)
        self.assertNotEqual(report["source"]["before"]["fingerprint"], report["source"]["after"]["fingerprint"])

    def test_assume_unchanged_cannot_hide_a_change_during_verification(self):
        self.remote()
        self.git("push", "origin", "main")
        self.git("update-index", "--assume-unchanged", "result.txt")
        command = [sys.executable, "-c", "from pathlib import Path; assert Path('result.txt').read_text() == '4'; Path('result.txt').write_text('3')"]
        result, report = self.run_verify(checks=[command], extra=["--commit", self.head])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertFalse(report["source"]["unchanged_during_verification"])
        self.assertTrue(report["source"]["after"]["dirty"])
        self.assertFalse(report["delivery"]["matches_verified_source"])
        self.assertTrue(report["delivery"]["remote_confirmed"])

    def test_preexisting_hidden_worktree_change_does_not_match_a_pushed_commit(self):
        self.remote()
        self.git("push", "origin", "main")
        self.git("update-index", "--assume-unchanged", "result.txt")
        (self.cwd / "result.txt").write_text("3")
        command = [sys.executable, "-c", "from pathlib import Path; assert Path('result.txt').read_text() == '3'"]
        result, report = self.run_verify(checks=[command], extra=["--commit", self.head])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertTrue(report["source"]["unchanged_during_verification"])
        self.assertFalse(report["source"]["after"]["tracked_content_matches_index"])
        self.assertFalse(report["delivery"]["matches_verified_source"])

    def test_git_repository_environment_is_isolated_only_for_probes(self):
        unrelated = self.base / "unrelated"
        self.git("clone", "--no-hardlinks", str(self.cwd), str(unrelated))
        overrides = {"GIT_DIR": str(unrelated / ".git"), "GIT_WORK_TREE": str(unrelated)}
        command = [sys.executable, "-c", f"import os; from pathlib import Path; assert os.environ['GIT_DIR'] == {overrides['GIT_DIR']!r}; Path('result.txt').write_text('3')"]
        with patch.dict(os.environ, overrides):
            result, report = self.run_verify(checks=[command])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(report["source"]["after"]["root"], str(self.cwd))
        self.assertEqual(report["verification"][0]["state"], "succeeded")
        self.assertFalse(report["source"]["unchanged_during_verification"])

    def test_configured_worktree_outside_requested_cwd_is_unverified(self):
        unrelated = self.base / "unrelated"
        unrelated.mkdir()
        self.git("config", "core.worktree", str(unrelated))
        result, report = self.run_verify()
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(report["source"]["after"]["reason"], "git_root_does_not_contain_cwd")

    def test_probe_retains_injected_config_used_for_authentication(self):
        logs = self.base / "probe-logs"
        logs.mkdir()
        git = verify._Git(self.cwd, logs, time.monotonic() + 5, [0])
        environment = {
            "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "cm.authSentinel",
            "GIT_CONFIG_VALUE_0": "test-only-sentinel",
        }
        with patch.dict(os.environ, environment):
            stage, output = git.read("config", "--get", "cm.authSentinel")
        self.assertTrue(verify._ok(stage))
        self.assertEqual(output.strip(), b"test-only-sentinel")

    def test_missing_sparse_tracked_content_is_explicitly_unverified(self):
        self.git("update-index", "--skip-worktree", "result.txt")
        (self.cwd / "result.txt").unlink()
        result, report = self.run_verify(checks=[[sys.executable, "-c", "pass"]], artifacts=())
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(report["source"]["after"]["reason"], "sparse_tracked_content_not_observed")

    def test_tracked_symlink_target_is_bound_without_following_it(self):
        (self.cwd / "selected").symlink_to("result.txt")
        self.git("add", "selected")
        self.git("commit", "-m", "Track source link")
        self.git("update-index", "--assume-unchanged", "selected")
        command = [sys.executable, "-c", "from pathlib import Path; Path('selected').unlink(); Path('selected').symlink_to('check.py')"]
        result, report = self.run_verify(checks=[command])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertFalse(report["source"]["unchanged_during_verification"])

    def test_hashing_checks_the_deadline_between_chunks(self):
        source = self.base / "large-source"
        source.write_bytes(b"a" * (2 * 1024 * 1024))
        git = verify._Git(self.cwd, self.base, 1.0, [0])
        with patch.object(verify.time, "monotonic", side_effect=[0.0, 0.0, 2.0]):
            with self.assertRaises(TimeoutError):
                verify._digest(source, git)

    def test_subdirectory_checks_still_bind_sibling_source(self):
        subdir = self.cwd / "src"
        subdir.mkdir()
        command = [sys.executable, "-c", "from pathlib import Path; Path('../result.txt').write_text('changed')"]
        result, report = self.run_verify(cwd=subdir, checks=[command], artifacts=())
        self.assertEqual(result.returncode, 3)
        self.assertFalse(report["source"]["unchanged_during_verification"])

    def test_report_inside_worktree_does_not_invalidate_itself(self):
        result, report = self.run_verify(report="project/report.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(report["source"]["after"]["dirty"])

    def test_non_git_directory_does_not_claim_bound_source(self):
        non_git = self.base / "plain"
        non_git.mkdir()
        result, report = self.run_verify(cwd=non_git, checks=[[sys.executable, "-c", "pass"]], artifacts=())
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["source"]["after"]["state"], "unavailable")

    def test_artifact_symlink_is_rejected_before_any_check(self):
        (self.cwd / "link.txt").symlink_to(self.cwd / "result.txt")
        result, report = self.run_verify(artifacts=("link.txt",))
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)

    def test_total_timeout_cleans_a_detached_checker_child(self):
        late = self.base / "late-write"
        child = f"import time; from pathlib import Path; time.sleep(1); Path({str(late)!r}).write_text('late')"
        command = [sys.executable, "-c", f"import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', {child!r}], start_new_session=True); time.sleep(5)"]
        result, report = self.run_verify(checks=[command], extra=["--timeout", "0.6"])
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertEqual(report["status"], "timed_out")
        self.assertTrue(report["verification"][0]["cleanup_complete"])
        time.sleep(1.1)
        self.assertFalse(late.exists())

    def test_remote_confirmation_requires_actual_remote_observation(self):
        self.remote()
        self.git("push", "origin", "main")
        result, report = self.run_verify(extra=["--commit", self.head])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report["delivery"]["remote_confirmed"])
        self.assertTrue(report["delivery"]["matches_verified_source"])
        self.assertEqual(report["delivery"]["remote_head"], self.head)
        self.assertEqual(report["delivery"]["relation"], "tip")

    def test_cached_remote_ref_is_not_delivery_when_remote_branch_disappears(self):
        remote = self.remote()
        self.git("push", "origin", "main")
        self.git("update-ref", "-d", "refs/heads/main", cwd=remote)
        self.assertEqual(self.git("rev-parse", "origin/main").stdout.strip(), self.head)
        result, report = self.run_verify(extra=["--commit", self.head])
        self.assertEqual(result.returncode, 3)
        self.assertTrue(report["delivery"]["local_committed"])
        self.assertFalse(report["delivery"]["remote_confirmed"])
        self.assertEqual(report["delivery"]["reason"], "remote_branch_missing")

    def test_remote_advanced_branch_can_confirm_an_existing_ancestor(self):
        self.remote()
        (self.cwd / "later.txt").write_text("later")
        self.git("add", "later.txt")
        self.git("commit", "-m", "Later task")
        later = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("push", "origin", "main")
        self.git("reset", "--hard", self.head)
        result, report = self.run_verify(extra=["--commit", self.head])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["delivery"]["remote_head"], later)
        self.assertEqual(report["delivery"]["relation"], "ancestor")

    def test_local_replace_refs_do_not_forge_remote_ancestry(self):
        self.remote()
        self.git("push", "origin", "main")
        remote_tip = self.head
        self.git("checkout", "--orphan", "unrelated")
        self.git("commit", "-m", "Unrelated local history")
        local_head = self.git("rev-parse", "HEAD").stdout.strip()
        replacement = self.git(
            "commit-tree", f"{remote_tip}^{{tree}}", "-p", local_head,
            "-m", "Local replacement metadata",
        ).stdout.strip()
        self.git("replace", remote_tip, replacement)
        self.assertEqual(
            self.git("merge-base", "--is-ancestor", local_head, remote_tip, check=False).returncode, 0
        )
        result, report = self.run_verify(extra=["--commit", local_head])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["delivery"]["state"], "not_delivered")
        self.assertFalse(report["delivery"]["remote_confirmed"])

    def test_pushed_commit_does_not_verify_uncommitted_work(self):
        self.remote()
        self.git("push", "origin", "main")
        (self.cwd / "check.py").write_text("assert 2 + 2 == 4\n")
        result, report = self.run_verify(extra=["--commit", self.head])
        self.assertEqual(result.returncode, 3)
        self.assertTrue(report["delivery"]["remote_confirmed"])
        self.assertFalse(report["delivery"]["matches_verified_source"])
        self.assertEqual(report["next_action"], "check_delivery")

    def test_unpushed_local_commit_is_not_delivered(self):
        self.remote()
        self.git("push", "origin", "main")
        (self.cwd / "new.txt").write_text("new")
        self.git("add", "new.txt")
        self.git("commit", "-m", "Unpushed result")
        new_head = self.git("rev-parse", "HEAD").stdout.strip()
        result, report = self.run_verify(extra=["--commit", new_head])
        self.assertEqual(result.returncode, 1)
        self.assertTrue(report["delivery"]["matches_verified_source"])
        self.assertEqual(report["delivery"]["state"], "not_delivered")
        self.assertEqual(report["next_action"], "deliver")

    def test_unknown_remote_tip_does_not_guess_ancestry_or_update_tracking_ref(self):
        remote = self.remote()
        self.git("push", "origin", "main")
        other = self.base / "other"
        self.git("clone", "--branch", "main", str(remote), str(other))
        self.git("config", "user.name", "Other test", cwd=other)
        self.git("config", "user.email", "other@example.invalid", cwd=other)
        (other / "new.txt").write_text("new remote commit")
        self.git("add", "new.txt", cwd=other)
        self.git("commit", "-m", "Remote advanced", cwd=other)
        self.git("push", "origin", "main", cwd=other)
        remote_head = self.git("rev-parse", "HEAD", cwd=other).stdout.strip()
        result, report = self.run_verify(extra=["--commit", self.head])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["delivery"]["remote_head"], remote_head)
        self.assertFalse(report["delivery"]["remote_confirmed"])
        self.assertIn("remote_tip_not_available_locally", report["delivery"]["reason"])
        self.assertEqual(self.git("rev-parse", "origin/main").stdout.strip(), self.head)

    def test_remote_failure_does_not_erase_successful_check_evidence(self):
        self.git("remote", "add", "origin", str(self.base / "nonexistent.git"))
        result, report = self.run_verify(extra=["--commit", self.head])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["verification"][0]["state"], "succeeded")
        self.assertFalse(report["delivery"]["remote_confirmed"])
        self.assertEqual(report["delivery"]["reason"], "remote_not_observed")


if __name__ == "__main__":
    unittest.main()
