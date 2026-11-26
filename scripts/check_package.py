"""Install the built wheel in a fresh venv and exercise its actual public commands."""

from __future__ import annotations

import argparse
import configparser
import email.parser
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import tomllib
import venv
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def invoke(
    argv: list[str], cwd: Path, *, expected: int = 0,
    extra_environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    # Fixture Git commands must not inherit a caller's alternate repository,
    # index or injected config; every operation stays in the fresh test repo.
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.pop("CONTROL_MESH_T3_BINARY", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_NO_INDEX"] = "1"
    environment.update(extra_environment or {})
    result = subprocess.run(
        argv, cwd=cwd, env=environment, capture_output=True, text=True,
        timeout=60, check=False,
    )
    if result.returncode != expected:
        raise RuntimeError(
            f"Command {argv[0]} returned {result.returncode}, expected {expected}\n"
            f"{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    options = parser.parse_args()
    candidates = [options.wheel] if options.wheel else list((ROOT / "dist").glob("*.whl"))
    if len(candidates) != 1:
        parser.error("build exactly one wheel or pass --wheel explicitly")
    wheel = candidates[0].resolve(strict=True)
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        actual = {name for name in names if name.startswith("controlmesh/")}
        expected = {
            "controlmesh/__init__.py", "controlmesh/__main__.py", "controlmesh/execution.py",
            "controlmesh/workflow.py", "controlmesh/closeout.py",
            "controlmesh/t3.py", "controlmesh/verify.py",
        }
        if actual != expected or any(name.startswith("controlmesh_runtime/") for name in names):
            raise RuntimeError(f"Unexpected wheel code: {sorted(actual ^ expected)}")
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = email.parser.BytesParser().parsebytes(archive.read(metadata_name))
        if metadata["Version"] != project["version"]:
            raise RuntimeError("Built version does not match pyproject.toml")
        requirements = metadata.get_all("Requires-Dist", [])
        if any("extra ==" not in item for item in requirements):
            raise RuntimeError(f"Unexpected production dependencies: {requirements}")
        entries_name = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        entries = configparser.ConfigParser()
        entries.read_string(archive.read(entries_name).decode())
        if dict(entries["console_scripts"]) != project["scripts"]:
            raise RuntimeError("Installed command declarations do not match the project")

    with tempfile.TemporaryDirectory(prefix="cm-wheel-") as temporary:
        root = Path(temporary)
        environment = root / "environment"
        venv.EnvBuilder(with_pip=True).create(environment)
        binary = environment / ("Scripts" if os.name == "nt" else "bin")
        python = str(binary / ("python.exe" if os.name == "nt" else "python"))
        suffix = ".exe" if os.name == "nt" else ""
        cm = str(binary / f"cm{suffix}")
        invoke([python, "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)], root)
        missing = invoke([cm], root, expected=127)
        if "CONTROL_MESH_T3_BINARY" not in missing.stderr or "Traceback" in missing.stderr:
            raise RuntimeError("Missing T3 runtime was not reported with an actionable error")
        for command, arguments in (
            ("cm", ["--help"]), ("controlmesh", ["--version"]),
            ("cm-workflow", ["--help"]), ("cm-closeout", ["--help"]),
            ("cm-verify", ["--help"]),
        ):
            invoke([str(binary / f"{command}{suffix}"), *arguments], root)
        for command in ("verify", "run", "workflow", "closeout"):
            invoke([cm, command, "--help"], root)
        invoke([cm, "bot"], root, expected=2)
        invoke([python, "-I", "-m", "pip", "check"], root)

        # Opt in to the already installed, pinned upstream runtime. The default
        # wheel gate never downloads T3 or starts a server/provider implicitly.
        runtime_result = {"status": "not_requested", "opt_in": "CM_T3_TEST_BINARY"}
        selected_runtime = os.environ.get("CM_T3_TEST_BINARY")
        if selected_runtime:
            runtime = Path(selected_runtime).expanduser().resolve(strict=True)
            cache = Path(os.environ.get("CM_T3_TEST_CACHE", str(root / "t3-cache"))).expanduser()
            cache.mkdir(parents=True, exist_ok=True, mode=0o700)
            runtime_environment = {
                "CONTROL_MESH_T3_BINARY": str(runtime), "T3CODE_HOME": str(cache.resolve()),
                "T3CODE_TELEMETRY_ENABLED": "false", "DO_NOT_TRACK": "1",
                "T3CODE_OTEL_SDK_DISABLED": "true", "OTEL_SDK_DISABLED": "true",
            }
            version = invoke([cm, "t3", "--version"], root, extra_environment=runtime_environment)
            pinned = json.loads((ROOT / "package.json").read_text())["dependencies"]["t3"]
            if pinned not in version.stdout:
                raise RuntimeError("Installed wheel did not invoke the pinned T3 version")
            help_result = invoke(
                [cm, "t3", "thread", "--help"], root, extra_environment=runtime_environment,
            )
            if any(command not in help_result.stdout for command in ("start", "send", "show", "list")):
                raise RuntimeError("Installed wheel did not expose the upstream thread CLI")
            runtime_result = {"status": "passed", "version": pinned, "model_turns_requested": 0}

        work = root / "project"
        work.mkdir()
        (work / "task.md").write_text("Write the integer 4 to result.txt.\n")
        (work / "verify.py").write_text(
            "from pathlib import Path\nassert Path('result.txt').read_text() == '4'\n"
        )
        contract = [
            cm, "run", "--cwd", str(work), "--task", "task.md", "--timeout", "10",
            "--verify", shlex.join([python, "verify.py"]), "--artifact", "result.txt",
        ]
        correct = [python, "-c", "from pathlib import Path; Path('result.txt').write_text('4')"]
        incorrect = [python, "-c", "from pathlib import Path; Path('result.txt').write_text('3')"]
        passed = root / "passed.json"
        invoke([*contract, "--report", str(passed), "--", *correct], root)
        result = json.loads(passed.read_text())
        if result["status"] != "completed" or result["next_action"] != "deliver":
            raise RuntimeError(f"Correct output was not accepted: {result['status']}")
        failed = root / "failed.json"
        invoke([*contract, "--report", str(failed), "--", *incorrect], root, expected=1)
        result = json.loads(failed.read_text())
        if result["status"] != "needs_repair":
            raise RuntimeError("An exit-zero worker with wrong output was not rejected")

        # This path checks existing output directly, without a dummy execution
        # command or another agent turn. Source state belongs to a real Git repo.
        verify_work = root / "verify-project"
        verify_work.mkdir()
        invoke(["git", "init", "--quiet", str(verify_work)], root)
        (verify_work / "result.txt").write_text("4")
        (verify_work / "check.py").write_text(
            "from pathlib import Path\nassert Path('result.txt').read_text() == '4'\n"
        )
        invoke(["git", "add", "."], verify_work)
        empty_hooks = root / "empty-hooks"
        empty_hooks.mkdir()
        invoke([
            "git", "-c", "user.name=CM package check", "-c", "user.email=package@example.invalid",
            "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={empty_hooks}",
            "commit", "--quiet", "-m", "Package verification fixture",
        ], verify_work)
        verification = [
            cm, "verify", "--cwd", str(verify_work), "--timeout", "10",
            "--verify", shlex.join([python, "-B", "check.py"]), "--artifact", "result.txt",
        ]
        verified = root / "verified.json"
        invoke([*verification, "--report", str(verified)], root)
        result = json.loads(verified.read_text())
        if (
            result["status"] != "verified" or "execution" in result
            or not result["source"]["unchanged_during_verification"]
            or result["delivery"]["requested"]
        ):
            raise RuntimeError("Independent verification did not bind the existing correct output")
        (verify_work / "result.txt").write_text("3")
        rejected = root / "rejected.json"
        invoke([*verification, "--report", str(rejected)], root, expected=1)
        result = json.loads(rejected.read_text())
        if result["status"] != "needs_repair" or result["verification"][0]["state"] != "failed":
            raise RuntimeError("Independent verification did not reject the incorrect existing output")

    print(json.dumps({
        "wheel": wheel.name, "bytes": wheel.stat().st_size,
        "production_dependencies": 0, "installed_commands": len(project["scripts"]),
        "real_task": "passed", "false_success": "rejected",
        "missing_t3_runtime": "rejected", "t3_runtime": runtime_result,
        "independent_verification": "passed", "incorrect_existing_output": "rejected",
    }, indent=2))


if __name__ == "__main__":
    main()
