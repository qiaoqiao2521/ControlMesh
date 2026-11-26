"""Exercise the source entry point without any installed third-party packages."""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EntrypointTests(unittest.TestCase):
    def invoke(self, *arguments: str, env=None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", "-S", "-m", "controlmesh", *arguments],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=10, check=False,
        )

    def test_default_entrypoint_launches_t3_with_inherited_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "t3"
            executable.write_text(
                f"#!{sys.executable}\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n"
            )
            executable.chmod(0o700)
            env = {**os.environ, "CONTROL_MESH_T3_BINARY": str(executable)}
            default = self.invoke(env=env)
            self.assertEqual(default.returncode, 0, default.stderr)
            self.assertEqual(json.loads(default.stdout), [])
            forwarded = self.invoke("t3", "thread", "list", "--json", env=env)
            self.assertEqual(forwarded.returncode, 0, forwarded.stderr)
            self.assertEqual(json.loads(forwarded.stdout), ["thread", "list", "--json"])

    def test_help_is_available_without_installing_t3(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("T3 Code", result.stdout)
        self.assertIn("verify", result.stdout)

    def test_each_retained_command_has_independent_help(self):
        for arguments in (("verify", "--help"), ("run", "--help"), ("workflow", "--help"), ("closeout", "--help"), ("--version",)):
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
