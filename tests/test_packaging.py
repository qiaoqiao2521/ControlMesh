"""Exercise the source entry point without any installed third-party packages."""

from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EntrypointTests(unittest.TestCase):
    def invoke(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", "-S", "-m", "controlmesh", *arguments],
            cwd=ROOT, capture_output=True, text=True, timeout=10, check=False,
        )

    def test_default_entrypoint_is_usable_without_runtime_dependencies(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("run", result.stdout)
        self.assertIn("workflow", result.stdout)
        self.assertNotIn("Telegram", result.stdout)

    def test_each_retained_command_has_independent_help(self):
        for arguments in (("run", "--help"), ("workflow", "--help"), ("closeout", "--help"), ("--version",)):
            with self.subTest(arguments=arguments):
                result = self.invoke(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.strip())
                self.assertNotIn("Traceback", result.stderr)

    def test_retired_bot_command_does_not_start_an_old_runtime(self):
        result = self.invoke("bot")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unknown_global_option_is_not_silently_ignored(self):
        result = self.invoke("--missing-option")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
