"""Explicit, offline cross-repository Markdown sync. Standard library only."""

import argparse
from contextlib import ExitStack
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import quote, urljoin, urlsplit


class ConflictError(ValueError):
    """A human-owned or ambiguous state that sync must preserve."""


def digest(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root), *args],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode:
        raise ConflictError(f"Git 无法读取 {root.name}，请检查仓库与提交")
    return result.stdout.strip()


def repo(value: str) -> Path:
    root = Path(value).expanduser().resolve(strict=True)
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ConflictError("配置必须指向 Git 仓库根目录")
    return root


def document(root: Path, value: str) -> Path:
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.suffix != ".md"
        or any(p.startswith((".", "-")) for p in relative.parts)
    ):
        raise ConflictError("只支持仓库内的普通 Markdown 路径")
    path = root
    for part in relative.parts:
        path /= part
        if path.is_symlink():
            raise ConflictError("不通过软链接读取或写入同步文档")
    path.resolve().relative_to(root)
    return path


def section(text: str, name: str) -> str:
    # A deliberately small input contract, not a Markdown inference engine.
    headings, fence, offset = [], "", 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (
                marker
                and marker[1][0] == fence[0]
                and len(marker[1]) >= len(fence)
                and not marker[2].strip()
            ):
                fence = ""
        elif marker:
            fence = marker[1]
        else:
            heading = re.match(r"^(#{1,2}) (.+?)\s*$", line)
            if heading:
                headings.append((len(heading[1]), heading[2], offset, offset + len(line)))
        offset += len(line)
    matches = [i for i, h in enumerate(headings) if h[0] == 2 and h[1] == name]
    if len(matches) != 1:
        raise ConflictError(f"需要唯一的二级标题：{name}")
    i = matches[0]
    end = headings[i + 1][2] if i + 1 < len(headings) else len(text)
    body = text[headings[i][3] : end].strip()
    if not body or re.search(r"(?m)^\s*(```|~~~)|<!--|<[^>]+>|\]\[|^\s*\[[^]]+\]:", body):
        raise ConflictError(
            "来源段落须为非空正文/列表与简单行内链接，不支持代码块、HTML、引用式链接"
        )
    return body


def render(body: str, base: str) -> str:
    pattern = r"(!?\[[^\]\n]*\])\(([^\s()]+)\)"

    def link(match: re.Match) -> str:
        target = urljoin(base, match[2])
        if urlsplit(target).scheme not in {"https", "http", "mailto"}:
            raise ConflictError("来源包含不支持的链接协议")
        return f"{match[1]}({target})"

    if re.search(r"\]\(", re.sub(pattern, "", body)):
        raise ConflictError("来源链接格式超出简单行内链接范围")
    return re.sub(pattern, link, body)


@dataclass
class Update:
    name: str
    root: Path
    path: Path
    before: bytes | None
    after: bytes
    source: Path
    source_bytes: bytes
    source_head: str
    source_root: Path

    @property
    def pending(self) -> bool:
        return self.before != self.after


def prepare(rule: dict, roots: dict[str, Path]) -> Update:
    name = rule["id"]
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise ConflictError("同步 ID 只允许小写字母、数字和连字符")
    source_root, target_root = roots[rule["source"]], roots[rule["target"]]
    source = document(source_root, rule["file"])
    target = document(target_root, rule["target_file"])
    if source == target:
        raise ConflictError("来源与目标不能是同一文件")
    head = git(source_root, "rev-parse", "HEAD")
    if git(source_root, "status", "--porcelain", "--", rule["file"]):
        raise ConflictError("来源文档尚未提交；请先完成该文档收尾")
    source_bytes = source.read_bytes()
    body = section(git(source_root, "show", f"{head}:{rule['file']}"), rule["section"])
    origin = git(source_root, "remote", "get-url", "origin")
    origin = origin.removesuffix(".git").replace("git@github.com:", "https://github.com/")
    if not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+", origin):
        raise ConflictError("首版来源须有 GitHub HTTPS/SSH origin，用于生成可追溯链接")
    fingerprint = digest(
        json.dumps([origin, rule["file"], rule["section"], body], ensure_ascii=False)
    )
    url = f"{origin}/blob/{head}/{quote(rule['file'])}"
    payload = f"\n来源：[{rule['source']} / {rule['section']}]({url})。此处为同步引用，验收边界以来源为准。\n\n{render(body, url)}\n"
    marker = f"<!-- cm-closeout:{name} "
    end = f"<!-- /cm-closeout:{name} -->"
    block = f"{marker}{fingerprint} {digest(payload)} -->{payload}{end}"
    before = target.read_bytes() if target.exists() else None
    if before is None:
        after = f"# {name}\n\n{block}\n".encode()
    else:
        text = before.decode("utf-8")
        if text.count(marker) != 1 or text.count(end) != 1:
            raise ConflictError("目标缺少唯一同步区域；不会覆盖或接管现有正文")
        pattern = re.escape(marker) + r"([0-9a-f]{64}) ([0-9a-f]{64}) -->(.*?)" + re.escape(end)
        match = re.search(pattern, text, re.DOTALL)
        if not match or digest(match[3]) != match[2]:
            raise ConflictError("同步区域被手改或标记损坏；请先保留并处理人工修改")
        after = (
            before
            if match[1] == fingerprint
            else (text[: match.start()] + block + text[match.end() :]).encode()
        )
    return Update(name, target_root, target, before, after, source, source_bytes, head, source_root)


def write(update: Update) -> None:
    path = document(update.root, update.path.relative_to(update.root).as_posix())
    current = path.read_bytes() if path.exists() else None
    if current != update.before:
        raise ConflictError("目标在检查后变化；保留并发修改，请重新检查")
    if (
        update.source.read_bytes() != update.source_bytes
        or git(update.source_root, "rev-parse", "HEAD") != update.source_head
    ):
        raise ConflictError("来源在检查后变化；请重新检查")
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, temporary = tempfile.mkstemp(prefix=".cm-closeout-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(update.after)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
        # This catches edits during the slow write/fsync phase too. Arbitrary
        # editors still need the user's single-closeout-writer convention.
        source_relative = update.source.relative_to(update.source_root).as_posix()
        if (
            git(update.source_root, "status", "--porcelain", "--", source_relative)
            or git(update.source_root, "rev-parse", "HEAD") != update.source_head
        ):
            raise ConflictError("来源在检查后变化；请重新检查")
        document(update.root, update.path.relative_to(update.root).as_posix())
        if (path.read_bytes() if path.exists() else None) != update.before:
            raise ConflictError("目标在检查后变化；保留并发修改，请重新检查")
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="任务收尾时按明确规则同步仓库状态；离线、零 Agent")
    parser.add_argument("action", choices=("check", "sync"))
    parser.add_argument(
        "--config", type=Path, default=Path.home() / ".config/controlmesh/closeout.json"
    )
    args = parser.parse_args(argv)
    written = 0
    try:
        config = json.loads(args.config.read_text())
        roots = {name: repo(path) for name, path in config["repositories"].items()}
        rules = config["links"]
        if not isinstance(rules, list) or not rules:
            raise ConflictError("请配置至少一条明确的同步关系")
        with ExitStack() as stack:
            # Serialize cooperating sync writers across configurations, in stable order.
            if args.action == "sync":
                lock_dirs = {
                    git(root, "rev-parse", "--absolute-git-dir") for root in roots.values()
                }
                for directory in sorted(lock_dirs):
                    lock = stack.enter_context((Path(directory) / "cm-closeout.lock").open("a"))
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            updates, errors = [], []
            for rule in rules:
                try:
                    updates.append(prepare(rule, roots))
                except (ConflictError, KeyError, TypeError, OSError, UnicodeError) as error:
                    errors.append(
                        f"阻塞 {rule.get('id', '?') if isinstance(rule, dict) else '?'}：{error}"
                    )
            if len({u.path for u in updates}) != len(updates) or len(
                {u.name for u in updates}
            ) != len(updates):
                raise ConflictError("同步 ID 和目标文件必须各自唯一")
            if {u.path for u in updates} & {u.source for u in updates}:
                raise ConflictError("单次同步不支持链式回写；每条来源必须独立提交")
            if errors:
                print("\n".join(errors))
                return 2
            pending = [u for u in updates if u.pending]
            if args.action == "check" and pending:
                print("\n".join(f"待同步 {u.name} → {u.path.relative_to(u.root)}" for u in pending))
                return 1
            for update in pending:
                write(update)
                written += 1
            print(f"已同步 {len(pending)} 项；待提交。" if pending else "已一致。")
            return 0
    except (
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        OSError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"阻塞：{error}")
        if written:
            print(f"此前已同步 {written} 项并保留；处理阻碍后重跑即可继续。")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
