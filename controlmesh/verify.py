"""Verify an existing T3 workspace without starting or repeating an agent turn.

The report binds explicit checks to observed Git state. Delivery is a separate,
read-only observation of a named remote branch, never a push or a cached-ref guess.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import sys
import time
from typing import Any

from controlmesh.execution import (
    _at,
    _fingerprint,
    _project_file,
    _publish,
    _run,
    _seconds,
    _signals,
)


SCHEMA = "controlmesh.verification.v1"
_MAX_GIT_OUTPUT = 8 * 1024 * 1024
_GIT_REPOSITORY_ENV = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE", "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX",
    "GIT_SHALLOW_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cm verify", description="Check existing results; never launch an agent (Linux)."
    )
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True, help="New private JSON report")
    parser.add_argument("--verify", action="append", default=[], help="Existing check argv, parsed without a shell; repeatable")
    parser.add_argument("--artifact", action="append", default=[], help="Required regular file inside cwd; repeatable")
    parser.add_argument("--timeout", type=_seconds, default=900.0, help="Total check and observation budget")
    parser.add_argument("--commit", help="Optional local commit to confirm on a remote branch")
    parser.add_argument("--remote", default="origin", help="Configured remote name, used with --commit")
    parser.add_argument("--branch", default="main", help="Remote branch name, used with --commit")
    return parser


class _Git:
    def __init__(self, cwd: Path, logs: Path, deadline: float, abort: list[int]):
        self.cwd, self.logs, self.deadline, self.abort = cwd, logs, deadline, abort
        self.requested_cwd = cwd
        self.sequence = 0

    def run(self, *args: str) -> tuple[dict[str, Any], Path]:
        self.sequence += 1
        label = f"git-{self.sequence}"
        # Clear repository selectors only in this child. Verification commands
        # retain the caller's environment. SSH/askpass and injected Git config
        # may hold authentication and stay intact; root containment is checked.
        environment = [argument for name in sorted(_GIT_REPOSITORY_ENV) for argument in ("-u", name)]
        result = _run(
            ["env", *environment, "GIT_GRAFT_FILE=/dev/null", "git", "--no-replace-objects",
             "--no-optional-locks", "--no-pager", "-C", str(self.cwd), *args],
            self.cwd, self.logs, label, self.deadline, self.abort,
        )
        return result, self.logs / f"{label}.stdout.log"

    def read(self, *args: str) -> tuple[dict[str, Any], bytes]:
        result, path = self.run(*args)
        if result["state"] != "succeeded" or not result.get("cleanup_complete"):
            return result, b""
        with path.open("rb") as source:
            value = source.read(_MAX_GIT_OUTPUT + 1)
        if len(value) > _MAX_GIT_OUTPUT:
            return {**result, "state": "unavailable", "error": "git_output_too_large"}, b""
        return result, value


def _ok(stage: dict[str, Any]) -> bool:
    return stage["state"] == "succeeded" and stage.get("cleanup_complete") is True


def _budget(git: _Git) -> None:
    if git.abort[0]:
        raise InterruptedError("source observation interrupted")
    if time.monotonic() >= git.deadline:
        raise TimeoutError("source observation budget exhausted")


def _digest(path: Path, git: _Git, blob_algorithm: str | None = None) -> tuple[str, int, str | None]:
    """Read actual bytes with a bounded budget, independent of Git's stat cache."""
    _budget(git)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("expected a regular file")
        digest = hashlib.sha256()
        blob = hashlib.new(blob_algorithm) if blob_algorithm else None
        if blob is not None:
            blob.update(f"blob {before.st_size}\0".encode())
        size = 0
        while True:
            _budget(git)
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
            if blob is not None:
                blob.update(chunk)
        after = os.fstat(source.fileno())
        current = path.lstat()
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns
        ) or size != before.st_size or (before.st_dev, before.st_ino) != (
            current.st_dev, current.st_ino
        ):
            raise ValueError("file changed while being observed")
        _budget(git)
        return digest.hexdigest(), size, blob.hexdigest() if blob is not None else None


def _entry(root: Path, relative: str, git: _Git, blob_algorithm: str | None = None) -> tuple[list, str, str | None]:
    _budget(git)
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("source path escaped repository")
    path = root / relative
    # A tracked symlink itself is observed, but never follow a replaced parent.
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("source parent became a symlink")
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        target = os.fsencode(os.readlink(path))
        digest = hashlib.sha256(target).hexdigest()
        blob = None
        if blob_algorithm:
            blob = hashlib.new(blob_algorithm, f"blob {len(target)}\0".encode() + target).hexdigest()
        mode = "120000"
    elif stat.S_ISREG(info.st_mode):
        digest, _, blob = _digest(path, git, blob_algorithm)
        mode = "100755" if info.st_mode & stat.S_IXUSR else "100644"
    else:
        raise ValueError("nonregular source entry")
    after = path.lstat()
    if (info.st_dev, info.st_ino, info.st_mode, info.st_mtime_ns, info.st_ctime_ns) != (
        after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns, after.st_ctime_ns
    ):
        raise ValueError("source entry changed while being observed")
    _budget(git)
    return [relative, stat.S_IFMT(info.st_mode), info.st_mode & 0o777, digest], mode, blob


def _observe_artifact(root: Path, path: Path, git: _Git) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path.relative_to(root)), "exists": False}
    try:
        _project_file(root, path)
        digest, size, _ = _digest(path, git)
        result.update(exists=True, sha256=digest, size_bytes=size)
    except FileNotFoundError:
        result["error"] = "missing"
    except TimeoutError:
        result["error"] = "observation_timed_out"
    except InterruptedError:
        result["error"] = "observation_interrupted"
    except (OSError, ValueError):
        result["error"] = "not_a_readable_regular_file"
    return result


def _snapshot(git: _Git, exclude: tuple[Path, ...]) -> dict[str, Any]:
    """Bind actual tracked bytes and untracked contents without modifying Git."""
    git.cwd = git.requested_cwd
    root_stage, raw_root = git.read("rev-parse", "--show-toplevel")
    if not _ok(root_stage):
        return {"state": "unavailable", "reason": "git_workspace_not_observed", "probe": root_stage}
    root = Path(os.fsdecode(raw_root.rstrip(b"\n"))).resolve()
    if not git.requested_cwd.is_relative_to(root):
        return {"state": "unavailable", "reason": "git_root_does_not_contain_cwd"}
    git.cwd = root
    head_stage, head = git.read("rev-parse", "--verify", "HEAD")
    # An unborn Git repository still has a bindable index and working tree.
    if head_stage["state"] not in {"succeeded", "failed"} or not head_stage.get("cleanup_complete"):
        return {"state": "unavailable", "reason": "git_head_not_observed", "probe": head_stage}
    index_stage, index = git.read("ls-files", "--stage", "-v", "-z")
    diff_stage, diff_path = git.run(
        "diff", "--no-ext-diff", "--no-textconv", "--binary", "--no-renames", "--ignore-submodules=none"
    )
    names_stage, names = git.read("ls-files", "--others", "--exclude-standard", "--full-name", "-z")
    status_stage, tracked_status = git.read("status", "--porcelain=v1", "-z", "--untracked-files=no")
    stages = [index_stage, diff_stage, names_stage, status_stage]
    if any(not _ok(stage) for stage in stages):
        return {"state": "unavailable", "reason": "git_source_not_observed", "probes": stages}
    untracked, tracked = [], []
    matches_index = True
    try:
        for record in sorted(set(index.split(b"\0")) - {b""}):
            _budget(git)
            metadata, raw = record.split(b"\t", 1)
            flag, mode, oid, stage = metadata.decode("ascii").split()
            relative = os.fsdecode(raw)
            if mode == "160000":  # Gitlink contents are explicitly outside coverage.
                continue
            algorithm = {40: "sha1", 64: "sha256"}.get(len(oid))
            if algorithm is None:
                raise ValueError("unknown Git object format")
            try:
                entry, actual_mode, actual_oid = _entry(root, relative, git, algorithm)
            except FileNotFoundError:
                if flag.upper() == "S":
                    return {"state": "unavailable", "reason": "sparse_tracked_content_not_observed"}
                entry, actual_mode, actual_oid = [relative, "missing"], "missing", None
            tracked.append(entry)
            matches_index = matches_index and stage == "0" and mode == actual_mode and oid == actual_oid
        for raw in sorted(set(names.split(b"\0")) - {b""}):
            _budget(git)
            relative = os.fsdecode(raw)
            path = root / relative
            if any(path == ignored or ignored in path.parents for ignored in exclude):
                continue
            entry, _, _ = _entry(root, relative, git)
            untracked.append(entry)
        tracked_diff = _digest(diff_path, git)[0]
        _budget(git)
    except TimeoutError:
        return {"state": "unavailable", "reason": "source_observation_timed_out"}
    except InterruptedError:
        return {"state": "unavailable", "reason": "source_observation_interrupted"}
    except (OSError, ValueError):
        return {"state": "unavailable", "reason": "source_content_not_observed"}
    identity = {
        "root": str(root),
        "head": head.decode("ascii").strip() if _ok(head_stage) else None,
        "index_sha256": hashlib.sha256(index).hexdigest(),
        "tracked_diff_sha256": tracked_diff,
        "tracked_worktree_sha256": _fingerprint(tracked),
        "untracked_sha256": _fingerprint(untracked),
    }
    return {
        "state": "observed", **identity, "fingerprint": _fingerprint(identity),
        "dirty": bool(tracked_status or untracked or not matches_index),
        "tracked_content_matches_index": matches_index, "untracked_count": len(untracked),
        "coverage": "Git index, actual tracked working-tree bytes/modes/symlinks, and nonignored untracked contents; excludes this report/logs, ignored files, and submodule internals. Delivery requires raw tracked bytes to match index blobs (filtered worktrees may need separate verification).",
    }


def _delivery(git: _Git, commit: str, remote: str, branch: str) -> dict[str, Any]:
    value: dict[str, Any] = {
        "requested": True, "remote": remote, "branch": branch,
        "state": "unverified", "local_committed": False, "remote_confirmed": False,
        "observed_at": datetime.now(UTC).isoformat(),
    }
    ref = f"refs/heads/{branch}"
    ref_stage, _ = git.read("check-ref-format", ref)
    commit_stage, raw_commit = git.read("rev-parse", "--verify", "--end-of-options", f"{commit}^{{commit}}")
    remotes_stage, remotes = git.read("remote")
    if not _ok(ref_stage) or not _ok(commit_stage):
        return {**value, "reason": "invalid_branch_or_local_commit"}
    resolved = raw_commit.decode("ascii").strip()
    value.update(commit=resolved, local_committed=True)
    if not _ok(remotes_stage) or remote not in remotes.decode("utf-8").splitlines():
        return {**value, "reason": "configured_remote_not_found"}
    stage, raw = git.read("ls-remote", "--exit-code", "--heads", "--", remote, ref)
    value["probe"] = stage
    if not _ok(stage):
        reason = "remote_branch_missing" if stage["state"] == "failed" and stage["exit_code"] == 2 else "remote_not_observed"
        return {**value, "reason": reason}
    matches = [line.split(b"\t", 1)[0] for line in raw.splitlines() if line.endswith(b"\t" + ref.encode())]
    if len(matches) != 1:
        return {**value, "reason": "ambiguous_remote_observation"}
    tip = matches[0].decode("ascii")
    value["remote_head"] = tip
    if tip == resolved:
        return {**value, "state": "remote_confirmed", "remote_confirmed": True, "relation": "tip"}
    object_stage, _ = git.read("cat-file", "-e", f"{tip}^{{commit}}")
    if not _ok(object_stage):
        return {**value, "reason": "remote_tip_not_available_locally; fetch the branch and recheck ancestry"}
    ancestor_stage, _ = git.read("merge-base", "--is-ancestor", resolved, tip)
    if _ok(ancestor_stage):
        return {**value, "state": "remote_confirmed", "remote_confirmed": True, "relation": "ancestor"}
    if ancestor_stage["state"] == "failed" and ancestor_stage["exit_code"] == 1:
        shallow_stage, shallow = git.read("rev-parse", "--is-shallow-repository")
        if _ok(shallow_stage) and shallow.strip() == b"false":
            return {**value, "state": "not_delivered", "reason": "commit_not_on_observed_remote_branch"}
    return {**value, "reason": "remote_ancestry_not_confirmed"}


def _outcome(checks: list[dict], artifacts: list[dict], stable: bool, delivery: dict, abort: int) -> tuple[str, str, int]:
    if abort:
        return "interrupted", "review_interruption", 128 + abort
    if any(check.get("cleanup_complete") is False for check in checks):
        return "needs_repair", "diagnose_cleanup", 1
    if any(check["state"] == "timed_out" for check in checks):
        return "timed_out", "diagnose_timeout", 124
    if any(check["state"] == "failed" for check in checks) or any(not item["exists"] for item in artifacts):
        return "needs_repair", "repair", 1
    if not checks or any(not _ok(check) for check in checks):
        return "unverified", "verify", 3
    if not stable:
        return "unverified", "verify_current_source", 3
    if delivery.get("requested"):
        if delivery["state"] == "not_delivered":
            return "needs_repair", "deliver", 1
        if not delivery["remote_confirmed"] or not delivery["matches_verified_source"]:
            return "unverified", "check_delivery", 3
    return "verified", "deliver", 0


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    try:
        if not sys.platform.startswith("linux"):
            raise ValueError("cm verify currently requires Linux for owned process cleanup")
        cwd = options.cwd.expanduser().resolve(strict=True)
        if not cwd.is_dir():
            raise ValueError("cwd must be an existing directory")
        checks_argv = [shlex.split(value) for value in options.verify]
        if any(not command or any("\0" in arg for arg in command) for command in checks_argv):
            raise ValueError("verification commands must not be empty")
        artifacts = list(dict.fromkeys(_project_file(cwd, path) for path in options.artifact))
        report_path = _at(cwd, options.report)
        report_path = report_path.parent.resolve(strict=True) / report_path.name
        logs = report_path.with_name(report_path.name + ".logs")
        if os.path.lexists(report_path) or os.path.lexists(logs):
            raise ValueError("report and log paths must be new")
        if any(path == report_path or path == logs or logs in path.parents for path in artifacts):
            raise ValueError("report/log paths overlap an artifact")
        logs.mkdir(mode=0o700)
        abort = [0]
        started_at = datetime.now(UTC).isoformat()
        with _signals(abort):
            deadline = time.monotonic() + options.timeout
            git = _Git(cwd, logs, deadline, abort)
            before = _snapshot(git, (report_path, logs))
            checks = []
            for index, command in enumerate(checks_argv):
                check = _run(command, cwd, logs, f"verify-{index + 1}", deadline, abort)
                checks.append(check)
                if check["state"] in {"interrupted", "timed_out"} or check.get("cleanup_complete") is False:
                    break
            observed = [_observe_artifact(cwd, path, git) for path in artifacts]
            after = _snapshot(git, (report_path, logs))
            stable = before.get("state") == after.get("state") == "observed" and before["fingerprint"] == after["fingerprint"]
            delivery = _delivery(git, options.commit, options.remote, options.branch) if options.commit else {"requested": False}
            if delivery["requested"]:
                delivery["matches_verified_source"] = bool(
                    stable and not after.get("dirty") and delivery.get("commit") == after.get("head")
                )
            status, action, code = _outcome(checks, observed, stable, delivery, abort[0])
            if not abort[0] and time.monotonic() >= deadline:
                status, action, code = "timed_out", "diagnose_timeout", 124
            report = {
                "schema_version": SCHEMA, "cwd": str(cwd),
                "started_at": started_at, "finished_at": datetime.now(UTC).isoformat(),
                "status": status, "next_action": action, "advisory": True,
                "verification": checks, "artifacts": observed,
                "source": {"before": before, "after": after, "unchanged_during_verification": stable},
                "delivery": delivery, "logs_directory": logs.name,
                "limits": "Only explicit checks and declared artifacts were verified. Source identity excludes ignored files and submodule internals. Remote delivery is a point-in-time observation, not a deployment or visual acceptance claim.",
            }
            _publish(report_path, report)
        print(json.dumps({"status": status, "next_action": action, "report": str(report_path), "advisory": True}))
        return code
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"error": "invalid_verification_request", "detail": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
