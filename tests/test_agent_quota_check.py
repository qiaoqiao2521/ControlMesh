"""Regression checks for the CLI quota probe's observed failure modes."""
import unittest
import importlib.util
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
