"""Regression checks for the CLI quota probe's observed failure modes."""
import unittest
import importlib.util
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("quota_check", Path(__file__).parents[1] / "scripts/agent_quota_check.py")
quota_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quota_check)


class QuotaCheckTests(unittest.TestCase):
    def test_cbc_exit_zero_does_not_hide_quota_error(self):
        assert quota_check.classify("", "429 额度已用尽", 0, "probe") == "quota_blocked"


    def test_empty_done_and_echoed_prompt_are_not_success(self):
        assert quota_check.classify('{"status":"done","result":""}', "", 0, "probe") == "unknown"
        assert quota_check.classify('{"prompt":"probe"}', "", 0, "probe") == "unknown"


    def test_success_accepts_native_text_and_json(self):
        assert quota_check.classify("probe\n", "", 0, "probe") == "ready"
        assert quota_check.classify('{"result":"probe","is_error":false}', "", 0, "probe") == "ready"


    def test_rate_limit_is_distinct_from_exhausted_balance(self):
        assert quota_check.classify("", "HTTP 429 Too many requests", 0, "probe") == "rate_limited"

    def test_prefers_ready_candidate_then_qoder_when_both_ready(self):
        checks = [{"agent": "qoder", "status": "quota_blocked", "usable": False},
                  {"agent": "agy", "status": "ready", "usable": True}]
        assert quota_check.pick(checks)["selected"] == "agy"
        checks[0].update(status="ready", usable=True)
        assert quota_check.pick(checks)["selected"] == "qoder"
        assert quota_check.pick(checks)["degraded"] is False

    def test_both_failed_selects_once_without_changing_probe_evidence(self):
        checks = [{"agent": "qoder", "status": "quota_blocked", "usable": False},
                  {"agent": "agy", "status": "timeout", "usable": False}]
        assert quota_check.pick(checks) == {"selected": "qoder", "degraded": True, "checks": checks}
        assert not any(item["usable"] for item in checks)

    def test_unconfigured_primary_falls_back_to_configured_cli(self):
        checks = [{"agent": "qoder", "status": "unconfigured", "usable": False},
                  {"agent": "agy", "status": "unknown", "usable": False}]
        assert quota_check.pick(checks)["selected"] == "agy"

    def test_agy_uses_native_flags_and_prompt_follows_print(self):
        def run(command, **kwargs):
            assert command[0] == "/fake/agy"
            assert command[-2] == "--print"
            assert "--tools" not in command
            assert "--no-session-persistence" not in command
            assert kwargs["timeout"] == 12
            return SimpleNamespace(stdout="quota_probe_test\n", stderr="", returncode=0)
        with patch.object(quota_check.secrets, "token_hex", return_value="test"), \
             patch.object(quota_check.subprocess, "run", side_effect=run):
            assert quota_check.check("agy", {"command": "/fake/agy"}, 12)["usable"]

    def test_timeout_and_missing_command_do_not_become_ready(self):
        with patch.object(quota_check.subprocess, "run", side_effect=quota_check.subprocess.TimeoutExpired("agy", 1)):
            assert quota_check.check("agy", {"command": "/fake/agy"}, 1)["status"] == "timeout"
        assert quota_check.check("agy", {}, 1)["status"] == "unavailable"

    def test_pick_cli_preserves_json_and_warns_when_both_probes_fail(self):
        checks = [{"agent": agent, "status": "quota_blocked", "usable": False}
                  for agent in ("qoder", "agy")]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(quota_check.sys, "argv", ["probe", "--pick"]), \
             patch.object(Path, "read_text", return_value=json.dumps({"agents": {"qoder": {"command": "qoder"}, "agy": {"command": "agy"}}})), \
             patch.object(quota_check, "check", side_effect=checks) as check, \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            quota_check.main()
        assert [call.args[0] for call in check.call_args_list] == ["qoder", "agy"]
        assert json.loads(stdout.getvalue()) == {"selected": "qoder", "degraded": True, "checks": checks}
        assert "WARNING" in stderr.getvalue()


if __name__ == "__main__":
    unittest.main()
