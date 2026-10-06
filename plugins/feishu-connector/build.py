#!/usr/bin/env python3
"""Rebuild the selected local Feishu plugin from its pinned npm archive."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

SOURCE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SOURCE_DIR.parents[1]
UPSTREAM_URL = (
    "https://registry.npmjs.org/@niubitli/plugin-feishu-connector/-/"
    "plugin-feishu-connector-0.3.11-connector-feishu.tgz"
)
UPSTREAM_SHA256 = "dac91409329a4005e12b59c0bf17c357a17fc7c0e7998a093624a1c289850cf3"
COMPAT_PATCH = REPOSITORY_ROOT / "plans/paperclip-feishu-canary/evidence/plugin-candidate.patch"
NATIVE_FILES = ("native-conversation.mjs", "native-conversation-cli.py")
COMPAT_VERSION = "0.3.11-connector-feishu.cm-compat.6"
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_UNPACKED_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 1024


class BuildError(RuntimeError):
    """A build prerequisite or the selected artifact was rejected."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_archive(destination: Path) -> None:
    """Download only the pinned package, with a bounded response size."""
    # The URL is a fixed HTTPS npm registry address; the archive hash is independently pinned.
    request = urllib.request.Request(UPSTREAM_URL, headers={"User-Agent": "cm-feishu-build"})  # noqa: S310
    try:
        with (
            urllib.request.urlopen(request, timeout=30) as response,  # noqa: S310
            destination.open("xb") as stream,
        ):
            received = 0
            while chunk := response.read(1024 * 1024):
                received += len(chunk)
                if received > MAX_ARCHIVE_BYTES:
                    raise BuildError("Upstream archive exceeds the size limit.")
                stream.write(chunk)
    except BuildError:
        raise
    except OSError as error:
        raise BuildError(f"Could not download the pinned npm archive: {error}") from error


def extract_archive(archive: Path, destination: Path) -> Path:
    """Extract regular files under package/; reject links and path traversal."""
    total_size = 0
    seen: set[PurePosixPath] = set()
    try:
        with tarfile.open(archive, mode="r:gz") as bundle:
            members = bundle.getmembers()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise BuildError("Archive contains too many members.")
            for member in members:
                path = PurePosixPath(member.name)
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or not path.parts
                    or path.parts[0] != "package"
                    or "\\" in member.name
                ):
                    raise BuildError(f"Unsafe archive path: {member.name}")
                if not (member.isfile() or member.isdir()):
                    raise BuildError(f"Unsupported archive entry: {member.name}")
                if path in seen:
                    raise BuildError(f"Duplicate archive path: {member.name}")
                seen.add(path)
                total_size += member.size
                if total_size > MAX_UNPACKED_BYTES:
                    raise BuildError("Archive exceeds the unpacked size limit.")
            # Validate the entire archive before creating any extracted file.
            for member in members:
                target = destination.joinpath(*PurePosixPath(member.name).parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is None:
                    raise BuildError(f"Archive file has no contents: {member.name}")
                with source, target.open("xb") as stream:
                    shutil.copyfileobj(source, stream)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
    except (tarfile.TarError, OSError) as error:
        raise BuildError(f"Could not safely extract the npm archive: {error}") from error
    package_dir = destination / "package"
    if not (package_dir / "package.json").is_file():
        raise BuildError("Archive has no package/package.json.")
    return package_dir


def apply_compat_patch(package_dir: Path) -> None:
    """Apply the repository's exact compatibility patch without fuzzy matches."""
    try:
        result = subprocess.run(
            ["patch", "-p1", "--batch", "--forward", "--fuzz=0"],
            input=COMPAT_PATCH.read_bytes(),
            cwd=package_dir,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise BuildError(f"Could not apply the compatibility patch: {error}") from error
    if result.returncode:
        detail = (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()
        raise BuildError(f"Compatibility patch failed: {detail}")
    for source_map in package_dir.glob("dist/**/*.map"):
        source_map.unlink()
    for rejected in package_dir.rglob("*.rej"):
        raise BuildError(f"Compatibility patch left a rejected hunk: {rejected.name}")
    for backup in package_dir.rglob("*.orig"):
        backup.unlink()


def extend_package(package_dir: Path) -> None:
    """Apply native conversation hooks, then copy the reviewed native modules."""
    transform_path = SOURCE_DIR / "transform.py"
    if transform_path.is_symlink() or not transform_path.is_file():
        raise BuildError("Native conversation transform must be a regular source file.")
    specification = importlib.util.spec_from_file_location("cm_feishu_transform", transform_path)
    if specification is None or specification.loader is None:
        raise BuildError("Native conversation transform could not be loaded.")
    transform = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(transform)
        for filename, function_name in (
            ("worker.js", "transform_worker"),
            ("manifest.js", "transform_manifest"),
        ):
            operation = getattr(transform, function_name, None)
            if not callable(operation):
                raise BuildError(f"Native conversation transform has no {function_name}.")
            destination = package_dir / "dist" / filename
            original = destination.read_text(encoding="utf-8")
            transformed = operation(original)
            if (
                not isinstance(transformed, str)
                or not transformed.strip()
                or transformed == original
            ):
                raise BuildError(f"Native conversation transform did not change {filename}.")
            if filename == "manifest.js":
                anchor = 'var PLUGIN_VERSION = "0.3.11-connector-feishu.cm-compat.5";'
                if transformed.count(anchor) != 1:
                    raise BuildError(
                        "Manifest must contain exactly one compatibility version anchor."
                    )
                transformed = transformed.replace(
                    anchor, f'var PLUGIN_VERSION = "{COMPAT_VERSION}";', 1
                )
            destination.write_text(transformed, encoding="utf-8")
    except BuildError:
        raise
    except Exception as error:
        raise BuildError(f"Native conversation transform failed: {error}") from error
    metadata_path = package_dir / "package.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["version"] = COMPAT_VERSION
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    for filename in NATIVE_FILES:
        source = SOURCE_DIR / filename
        if source.is_symlink() or not source.is_file():
            raise BuildError(f"Native module must be a regular source file: {filename}")
        destination = package_dir / "dist" / filename
        if destination.exists() or destination.is_symlink():
            raise BuildError(f"Native module would replace an upstream file: {filename}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o755 if filename.endswith(".py") else 0o644)


def validate_package(package_dir: Path) -> dict:
    try:
        metadata = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BuildError(f"Generated package metadata is invalid: {error}") from error
    if metadata.get("name") != "@niubitli/plugin-feishu-connector":
        raise BuildError("Generated package has an unexpected identity.")
    if metadata.get("version") != COMPAT_VERSION:
        raise BuildError("Generated package has an unexpected compatibility version.")
    if metadata.get("private") is not True:
        raise BuildError("Generated compatibility package must remain private.")
    if metadata.get("peerDependencies", {}).get("@paperclipai/plugin-sdk") != "2026.916.1":
        raise BuildError("Generated package does not pin the selected host SDK.")
    for filename in ("dist/worker.js", "dist/manifest.js"):
        if not (package_dir / filename).is_file():
            raise BuildError(f"Generated package is missing {filename}.")
    return metadata


def build_plugin(output: Path, tarball: Path | None = None) -> dict:
    """Build in isolation, then publish into a newly created output directory."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise BuildError("Output already exists; select a new build directory.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cm-feishu-build-", dir=output.parent) as temporary:
        staging = Path(temporary)
        archive = tarball or staging / "upstream.tgz"
        if tarball is None:
            download_archive(archive)
        if not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE_BYTES:
            raise BuildError("Selected archive is missing or exceeds the size limit.")
        if sha256_file(archive) != UPSTREAM_SHA256:
            raise BuildError("Selected archive SHA-256 does not match the pinned npm package.")
        package_dir = extract_archive(archive, staging / "unpacked")
        apply_compat_patch(package_dir)
        extend_package(package_dir)
        metadata = validate_package(package_dir)
        receipt = {
            "upstreamUrl": UPSTREAM_URL,
            "upstreamSha256": UPSTREAM_SHA256,
            "compatPatchSha256": sha256_file(COMPAT_PATCH),
            "nativeTransformSha256": sha256_file(SOURCE_DIR / "transform.py"),
            "version": metadata.get("version"),
            "files": {
                str(path.relative_to(package_dir)): sha256_file(path)
                for path in sorted(package_dir.rglob("*"))
                if path.is_file()
            },
        }
        (package_dir / "CM-BUILD.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        # mkdir is exclusive even if another process created the target during the build.
        try:
            output.mkdir()
        except FileExistsError as error:
            raise BuildError(
                "Output was created by another process; nothing was replaced."
            ) from error
        try:
            shutil.copytree(package_dir, output, dirs_exist_ok=True)
        except BaseException:
            shutil.rmtree(output)
            raise
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tarball", type=Path, help="Use a local copy of the pinned npm archive.")
    parser.add_argument("--output", required=True, type=Path, help="New output package directory.")
    args = parser.parse_args()
    try:
        receipt = build_plugin(args.output, args.tarball)
    except (BuildError, OSError) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(
        json.dumps({"output": str(args.output.absolute()), **receipt}, ensure_ascii=False, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
