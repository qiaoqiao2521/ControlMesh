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


def invoke(argv: list[str], cwd: Path, *, expected: int = 0) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_NO_INDEX"] = "1"
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
        for command, arguments in (
            ("cm", ["--help"]), ("controlmesh", ["--version"]),
            ("cm-workflow", ["--help"]), ("cm-closeout", ["--help"]),
        ):
            invoke([str(binary / f"{command}{suffix}"), *arguments], root)
        for command in ("run", "workflow", "closeout"):
            invoke([cm, command, "--help"], root)
        invoke([cm, "bot"], root, expected=2)
        invoke([python, "-I", "-m", "pip", "check"], root)

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

    print(json.dumps({
        "wheel": wheel.name, "bytes": wheel.stat().st_size,
        "production_dependencies": 0, "installed_commands": 4,
        "real_task": "passed", "false_success": "rejected",
    }, indent=2))


if __name__ == "__main__":
    main()
