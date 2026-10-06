"""Offline checks for archive containment and reproducible compatibility builds."""
# Tests intentionally remain executable with Python's standard library.
# ruff: noqa: INP001, PT009, PT027

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BUILD_PATH = Path(__file__).resolve().parents[1] / "build.py"
SPEC = importlib.util.spec_from_file_location("cm_feishu_plugin_build", BUILD_PATH)
assert SPEC is not None
assert SPEC.loader is not None
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


def make_archive(path: Path, entries: list[tuple[tarfile.TarInfo, bytes]]) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for entry, content in entries:
            entry.size = len(content) if entry.isfile() else 0
            archive.addfile(entry, io.BytesIO(content) if entry.isfile() else None)


def file_entry(name: str, content: bytes) -> tuple[tarfile.TarInfo, bytes]:
    entry = tarfile.TarInfo(name)
    entry.mode = 0o644
    return entry, content


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.archive = self.root / "fixture.tgz"
        self.output = self.root / "output"
        self.source_dir = self.root / "source"
        self.source_dir.mkdir()

    def prepare_fixture(self) -> Path:
        metadata = {
            "name": "@niubitli/plugin-feishu-connector",
            "version": "fixture.cm-compat.5",
            "private": True,
            "peerDependencies": {"@paperclipai/plugin-sdk": "2026.916.1"},
        }
        make_archive(
            self.archive,
            [
                file_entry("package/package.json", (json.dumps(metadata) + "\n").encode()),
                file_entry("package/dist/worker.js", b"// upstream\n"),
                file_entry(
                    "package/dist/manifest.js",
                    b'var PLUGIN_VERSION = "0.3.11-connector-feishu.cm-compat.5";\nexport default {};\n',
                ),
                file_entry("package/dist/worker.js.map", b"{}"),
            ],
        )
        compat_patch = self.root / "compat.patch"
        compat_patch.write_text(
            "--- a/dist/worker.js\n+++ b/dist/worker.js\n"
            "@@ -1 +1 @@\n-// upstream\n+// compatibility\n"
        )
        (self.source_dir / "transform.py").write_text(
            "def transform_worker(source):\n"
            "    assert source == '// compatibility\\n'\n"
            "    return source + '// native hook executed\\n'\n"
            "def transform_manifest(source):\n"
            "    return source + '// native config schema\\n'\n"
        )
        (self.source_dir / "native-conversation.mjs").write_text("export const mode = 'native';\n")
        (self.source_dir / "native-conversation-cli.py").write_text("#!/usr/bin/python3\n")
        return compat_patch

    def fixture_build(self, compat_patch: Path) -> dict:
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        with (
            patch.object(build, "UPSTREAM_SHA256", digest),
            patch.object(build, "COMPAT_PATCH", compat_patch),
            patch.object(build, "SOURCE_DIR", self.source_dir),
        ):
            return build.build_plugin(self.output, self.archive)

    def test_build_applies_exact_patch_copies_native_source_and_records_hashes(self) -> None:
        compat_patch = self.prepare_fixture()
        source = self.source_dir / "native-conversation.mjs"
        source.write_text("export const mode = 'native';\n")
        receipt = self.fixture_build(compat_patch)
        self.assertEqual(
            (self.output / "dist/worker.js").read_text(),
            "// compatibility\n// native hook executed\n",
        )
        self.assertIn("native config schema", (self.output / "dist/manifest.js").read_text())
        self.assertIn(
            'var PLUGIN_VERSION = "0.3.11-connector-feishu.cm-compat.6";',
            (self.output / "dist/manifest.js").read_text(),
        )
        self.assertEqual(
            (self.output / "dist/native-conversation.mjs").read_bytes(), source.read_bytes()
        )
        self.assertFalse((self.output / "dist/worker.js.map").exists())
        persisted = json.loads((self.output / "CM-BUILD.json").read_text())
        self.assertEqual(receipt, persisted)
        self.assertEqual(
            receipt["files"]["dist/native-conversation.mjs"], build.sha256_file(source)
        )
        self.assertEqual(
            receipt["nativeTransformSha256"], build.sha256_file(self.source_dir / "transform.py")
        )
        self.assertEqual(receipt["version"], "0.3.11-connector-feishu.cm-compat.6")
        self.assertEqual(
            json.loads((self.output / "package.json").read_text())["version"], receipt["version"]
        )
        self.assertTrue((self.output / "dist/native-conversation-cli.py").stat().st_mode & 0o111)

    def test_existing_output_is_not_modified(self) -> None:
        self.output.mkdir()
        protected = self.output / "running-worker.js"
        protected.write_text("existing runtime")
        with self.assertRaisesRegex(build.BuildError, "already exists"):
            build.build_plugin(self.output, self.archive)
        self.assertEqual(protected.read_text(), "existing runtime")

    def test_dangling_output_symlink_is_rejected(self) -> None:
        self.output.symlink_to(self.root / "absent", target_is_directory=True)
        with self.assertRaisesRegex(build.BuildError, "already exists"):
            build.build_plugin(self.output, self.archive)
        self.assertTrue(self.output.is_symlink())

    def test_wrong_checksum_is_rejected_before_extract_or_patch(self) -> None:
        self.prepare_fixture()
        with (
            patch.object(build, "extract_archive") as extract,
            self.assertRaisesRegex(build.BuildError, "SHA-256"),
        ):
            build.build_plugin(self.output, self.archive)
        extract.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_unsafe_paths_are_rejected_before_any_extraction(self) -> None:
        for name in (
            "/tmp/escaped",
            "package/../../escaped",
            "other/package.json",
            "package\\evil",
        ):
            with self.subTest(name=name):
                make_archive(
                    self.archive,
                    [file_entry("package/package.json", b"{}"), file_entry(name, b"bad")],
                )
                destination = self.root / "extracted"
                with self.assertRaisesRegex(build.BuildError, "Unsafe archive path"):
                    build.extract_archive(self.archive, destination)
                self.assertFalse(destination.exists())

    def test_links_and_special_entries_are_rejected(self) -> None:
        for entry_type in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE):
            with self.subTest(entry_type=entry_type):
                member = tarfile.TarInfo("package/linked")
                member.type = entry_type
                member.linkname = "../../outside"
                make_archive(
                    self.archive, [file_entry("package/package.json", b"{}"), (member, b"")]
                )
                with self.assertRaisesRegex(build.BuildError, "Unsupported archive entry"):
                    build.extract_archive(self.archive, self.root / "extracted")

    def test_duplicate_archive_path_is_rejected(self) -> None:
        make_archive(
            self.archive,
            [
                file_entry("package/package.json", b"{}"),
                file_entry("package/package.json", b"replacement"),
            ],
        )
        with self.assertRaisesRegex(build.BuildError, "Duplicate archive path"):
            build.extract_archive(self.archive, self.root / "extracted")

    def test_unpacked_size_limit_is_enforced(self) -> None:
        make_archive(self.archive, [file_entry("package/package.json", b"oversized")])
        with (
            patch.object(build, "MAX_UNPACKED_BYTES", 2),
            self.assertRaisesRegex(build.BuildError, "unpacked size limit"),
        ):
            build.extract_archive(self.archive, self.root / "extracted")

    def test_failed_patch_does_not_publish_output(self) -> None:
        compat_patch = self.prepare_fixture()
        compat_patch.write_text(
            "--- a/dist/worker.js\n+++ b/dist/worker.js\n"
            "@@ -1 +1 @@\n-// unexpected base\n+// replacement\n"
        )
        with self.assertRaisesRegex(build.BuildError, "Compatibility patch failed"):
            self.fixture_build(compat_patch)
        self.assertFalse(self.output.exists())

    def test_native_source_symlink_is_not_copied(self) -> None:
        compat_patch = self.prepare_fixture()
        secret = self.root / "private.txt"
        secret.write_text("private fixture")
        (self.source_dir / "native-conversation.mjs").unlink()
        (self.source_dir / "native-conversation.mjs").symlink_to(secret)
        with self.assertRaisesRegex(build.BuildError, "regular source file"):
            self.fixture_build(compat_patch)
        self.assertFalse(self.output.exists())

    def test_missing_transform_does_not_publish_unintegrated_native_files(self) -> None:
        compat_patch = self.prepare_fixture()
        (self.source_dir / "transform.py").unlink()
        with self.assertRaisesRegex(build.BuildError, "transform must be a regular source file"):
            self.fixture_build(compat_patch)
        self.assertFalse(self.output.exists())

    def test_transform_anchor_failure_does_not_publish_output(self) -> None:
        compat_patch = self.prepare_fixture()
        (self.source_dir / "transform.py").write_text(
            "def transform_worker(source):\n"
            "    raise ValueError('Expected worker anchor is absent')\n"
            "def transform_manifest(source):\n"
            "    return source + '// transformed'\n"
        )
        with self.assertRaisesRegex(build.BuildError, "Expected worker anchor is absent"):
            self.fixture_build(compat_patch)
        self.assertFalse(self.output.exists())

    def test_unchanged_transform_is_rejected(self) -> None:
        compat_patch = self.prepare_fixture()
        (self.source_dir / "transform.py").write_text(
            "def transform_worker(source):\n    return source\n"
            "def transform_manifest(source):\n    return source\n"
        )
        with self.assertRaisesRegex(build.BuildError, "did not change worker.js"):
            self.fixture_build(compat_patch)
        self.assertFalse(self.output.exists())

    def test_package_without_private_flag_is_rejected(self) -> None:
        compat_patch = self.prepare_fixture()
        compat_patch.write_text(
            compat_patch.read_text() + "--- a/package.json\n+++ b/package.json\n@@ -1 +1 @@\n"
            '-{"name": "@niubitli/plugin-feishu-connector", "version": "fixture.cm-compat.5", '
            '"private": true, "peerDependencies": {"@paperclipai/plugin-sdk": "2026.916.1"}}\n'
            '+{"name": "@niubitli/plugin-feishu-connector", "version": "fixture", '
            '"private": false, "peerDependencies": {"@paperclipai/plugin-sdk": "2026.916.1"}}\n'
        )
        with self.assertRaisesRegex(build.BuildError, "remain private"):
            self.fixture_build(compat_patch)
        self.assertFalse(self.output.exists())


REAL_TARBALL = Path(
    os.environ.get(
        "CM_FEISHU_TARBALL",
        str(
            Path.home()
            / "Documents/Codex/2026-09-27/t/work/feishu-paperclip-20260930/plugin-audit/package.tgz"
        ),
    )
)


@unittest.skipUnless(
    REAL_TARBALL.is_file(),
    "Set CM_FEISHU_TARBALL to the pinned npm archive for real-package checks.",
)
class RealPackageTransformTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.assertEqual(build.sha256_file(REAL_TARBALL), build.UPSTREAM_SHA256)
        self.package = build.extract_archive(REAL_TARBALL, self.root / "baseline")
        build.apply_compat_patch(self.package)
        transform_spec = importlib.util.spec_from_file_location(
            "cm_feishu_real_transform", BUILD_PATH.parent / "transform.py"
        )
        assert transform_spec is not None
        assert transform_spec.loader is not None
        self.transform = importlib.util.module_from_spec(transform_spec)
        transform_spec.loader.exec_module(self.transform)

    def test_real_build_wires_native_hooks_and_matches_package_manifest_version(self) -> None:
        output = self.root / "package"
        receipt = build.build_plugin(output, REAL_TARBALL)
        worker = (output / "dist/worker.js").read_text()
        manifest = (output / "dist/manifest.js").read_text()
        self.assertIn("await cmNativeConversation.handle(ctx, config, connection, message)", worker)
        self.assertIn("await cmNativeConversation.flush(ctx, config)", worker)
        self.assertIn("validateNativeConversationConfig(config, incomingCompanyId)", worker)
        self.assertIn("nativeConversation: {", manifest)
        self.assertIn(f'var PLUGIN_VERSION = "{receipt["version"]}";', manifest)
        self.assertEqual(receipt["version"], build.COMPAT_VERSION)

    def test_worker_missing_duplicate_or_unscoped_anchor_is_rejected(self) -> None:
        worker = (self.package / "dist/worker.js").read_text()
        anchor = "  const sessionKey = buildSessionKey(message, connection.id);\n"
        candidates = (
            worker.replace(anchor, "  // missing dispatch anchor\n"),
            worker + "\n" + anchor,
            worker.replace("function cmScopedContext(", "function obsoleteContext("),
        )
        for candidate in candidates:
            with self.subTest(candidate_length=len(candidate)), self.assertRaises(ValueError):
                self.transform.transform_worker(candidate)

    def test_repeated_worker_and_manifest_transforms_are_rejected(self) -> None:
        for filename, operation in (
            ("worker.js", self.transform.transform_worker),
            ("manifest.js", self.transform.transform_manifest),
        ):
            with self.subTest(filename=filename):
                source = (self.package / "dist" / filename).read_text()
                transformed = operation(source)
                with self.assertRaisesRegex(ValueError, "already present"):
                    operation(transformed)


if __name__ == "__main__":
    unittest.main()
