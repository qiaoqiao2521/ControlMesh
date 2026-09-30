"""Cross-repository acceptance with temporary Git repositories, no provider runtime."""

import json
from pathlib import Path
import subprocess

import pytest

from controlmesh import closeout


def run_git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def workspace(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    for root in (source, target):
        root.mkdir()
        run_git(root, "init", "-q")
        run_git(root, "config", "user.email", "test@example.invalid")
        run_git(root, "config", "user.name", "Test")
    run_git(source, "remote", "add", "origin", "https://github.com/example/source.git")
    (source / "plans").mkdir()
    (source / "plans/progress.md").write_text(
        "# Progress\n\n## Current\n本机通过，生产待验收。[依据](../evidence.md)\n\n## Next\nLater\n"
    )
    run_git(source, "add", ".")
    run_git(source, "commit", "-qm", "Initial")
    config = tmp_path / "closeout.json"
    data = {
        "repositories": {"cm": str(source), "cap": str(target)},
        "links": [
            {
                "id": "cm-current",
                "source": "cm",
                "file": "plans/progress.md",
                "section": "Current",
                "target": "cap",
                "target_file": "facts.md",
            }
        ],
    }
    config.write_text(json.dumps(data))
    return source, target, config, data


def invoke(config, action):
    return closeout.main([action, "--config", str(config)])


def revise(source, body="本机和群聊通过，生产待验收。"):
    (source / "plans/progress.md").write_text(f"# Progress\n\n## Current\n{body}\n")
    run_git(source, "add", "plans/progress.md")
    run_git(source, "commit", "-qm", "Update status")


def test_real_check_sync_idempotency_and_provenance(workspace, capsys):
    source, target, config, _ = workspace
    before = sorted(str(p.relative_to(target)) for p in target.rglob("*"))
    index = source / ".git/index"
    index_before = (index.read_bytes(), index.stat().st_mtime_ns)
    assert invoke(config, "check") == 1
    assert (index.read_bytes(), index.stat().st_mtime_ns) == index_before
    assert sorted(str(p.relative_to(target)) for p in target.rglob("*")) == before
    assert invoke(config, "sync") == 0
    facts = target / "facts.md"
    data, mtime = facts.read_bytes(), facts.stat().st_mtime_ns
    sha = run_git(source, "rev-parse", "HEAD")
    assert f"/blob/{sha}/evidence.md".encode() in data
    assert "生产待验收".encode() in data
    assert invoke(config, "check") == 0
    assert invoke(config, "sync") == 0
    assert facts.read_bytes() == data
    assert facts.stat().st_mtime_ns == mtime
    assert capsys.readouterr().out.endswith("已一致。\n")


def test_unrelated_commit_does_not_refresh_old_provenance(workspace):
    source, target, config, _ = workspace
    assert invoke(config, "sync") == 0
    before = (target / "facts.md").read_bytes()
    (source / "other.md").write_text("Unrelated")
    run_git(source, "add", ".")
    run_git(source, "commit", "-qm", "Unrelated")
    assert invoke(config, "check") == 0
    assert invoke(config, "sync") == 0
    assert (target / "facts.md").read_bytes() == before


def test_changed_source_updates_only_managed_block(workspace):
    source, target, config, _ = workspace
    assert invoke(config, "sync") == 0
    facts = target / "facts.md"
    before = facts.read_bytes()
    facts.write_bytes(b"Owner notes\r\n" + before + b"\r\nKeep this.\r\n")
    facts.chmod(0o640)
    revise(source)
    assert invoke(config, "check") == 1
    assert invoke(config, "sync") == 0
    assert facts.read_bytes().startswith(b"Owner notes\r\n")
    assert facts.read_bytes().endswith(b"\r\nKeep this.\r\n")
    assert facts.stat().st_mode & 0o777 == 0o640
    assert "群聊通过" in facts.read_text()


@pytest.mark.parametrize("mutation", ["body", "marker", "duplicate", "existing"])
def test_human_content_never_overwritten(workspace, mutation):
    source, target, config, _ = workspace
    assert invoke(config, "sync") == 0
    facts = target / "facts.md"
    text = facts.read_text()
    if mutation == "body":
        text = text.replace("本机通过", "人工判断")
    elif mutation == "marker":
        text = text.replace("<!-- cm-closeout:", "<!-- changed:")
    elif mutation == "duplicate":
        text *= 2
    else:
        text = "Existing human document\n"
    facts.write_text(text)
    revise(source)
    assert invoke(config, "sync") == 2
    assert facts.read_text() == text


def test_uncommitted_source_blocks(workspace):
    source, target, config, _ = workspace
    (source / "plans/progress.md").write_text("## Current\nWIP\n")
    assert invoke(config, "sync") == 2
    assert not (target / "facts.md").exists()


@pytest.mark.parametrize(
    "body",
    ["", "[broken](a file.md)", "[link][ref]", "```sh\nexit\n```", "[bad](javascript:alert)"],
)
def test_unsupported_markdown_fails_closed(workspace, body):
    source, target, config, _ = workspace
    revise(source, body)
    assert invoke(config, "sync") == 2
    assert not (target / "facts.md").exists()


@pytest.mark.parametrize(
    "path", ["../outside.md", "/tmp/outside.md", ".git/config.md", "secrets.env"]
)
def test_paths_fail_closed(workspace, path):
    _, target, config, data = workspace
    data["links"][0]["target_file"] = path
    config.write_text(json.dumps(data))
    assert invoke(config, "sync") == 2
    assert not (target / "facts.md").exists()


def test_target_symlink_rejected(workspace, tmp_path):
    _, target, config, _ = workspace
    outside = tmp_path / "outside.md"
    outside.write_text("Keep")
    (target / "facts.md").symlink_to(outside)
    assert invoke(config, "sync") == 2
    assert outside.read_text() == "Keep"


def test_one_conflict_prevents_preflight_batch_write(workspace):
    _, target, config, data = workspace
    data["links"].append({**data["links"][0], "id": "second", "target_file": "existing.md"})
    config.write_text(json.dumps(data))
    (target / "existing.md").write_text("Owned")
    assert invoke(config, "sync") == 2
    assert not (target / "facts.md").exists()


def test_concurrent_target_edit_is_preserved(workspace):
    _, target, _, data = workspace
    update = closeout.prepare(
        data["links"][0], {k: Path(v) for k, v in data["repositories"].items()}
    )
    (target / "facts.md").write_text("Concurrent")
    with pytest.raises(closeout.ConflictError, match="目标在检查后变化"):
        closeout.write(update)
    assert (target / "facts.md").read_text() == "Concurrent"


def test_no_site_packages_or_provider_imports(workspace):
    _, _, config, _ = workspace
    result = subprocess.run(
        ["python3", "-S", "-m", "controlmesh.closeout", "check", "--config", str(config)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    assert "待同步" in result.stdout


def test_late_concurrent_edit_survives_fsync(workspace, monkeypatch):
    _, target, _, data = workspace
    update = closeout.prepare(
        data["links"][0], {k: Path(v) for k, v in data["repositories"].items()}
    )
    monkeypatch.setattr(
        closeout.os, "fsync", lambda _: (target / "facts.md").write_text("Late edit")
    )
    with pytest.raises(closeout.ConflictError, match="目标在检查后变化"):
        closeout.write(update)
    assert (target / "facts.md").read_text() == "Late edit"
    assert not list(target.glob(".cm-closeout-*"))


def test_source_change_during_write_stops_sync(workspace, monkeypatch):
    source, target, _, data = workspace
    update = closeout.prepare(
        data["links"][0], {k: Path(v) for k, v in data["repositories"].items()}
    )
    monkeypatch.setattr(
        closeout.os, "fsync", lambda _: (source / "plans/progress.md").write_text("WIP")
    )
    with pytest.raises(closeout.ConflictError, match="来源在检查后变化"):
        closeout.write(update)
    assert not (target / "facts.md").exists()


def test_fenced_example_is_not_selected():
    with pytest.raises(closeout.ConflictError, match="唯一的二级标题"):
        closeout.section("# Doc\n```md\n## State\nexample-only\n## Next\n```\n", "State")
    assert closeout.section("## State\nApproved\n# Private\nMust not copy\n", "State") == "Approved"
