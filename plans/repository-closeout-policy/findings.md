# Findings — 仓库收尾与交付规范落地

## 1. 共享规范修订与精确 Patch

共享规范 `/home/muqiao/.agents/AGENTS.md` 为不在 Git 追踪的本机核心规范文件。

- **修订前 SHA256**: `e7d0d6c14fb061574787ea52c7dd72d08ed4ac45d1dda8610e0508ee7d626fe2`
- **修订后 SHA256**: `fb1d564d8380a9fa66abf59a121e7f5b63dd336068f26fab0880058f6f6a9166`
- **原文件备份**: `/home/muqiao/Documents/Codex/2026-09-27/t/work/cm-closeout-policy-20260930/shared-AGENTS.before.md`

### 精确变更 Patch

```diff
--- /home/muqiao/.agents/AGENTS.md (before)
+++ /home/muqiao/.agents/AGENTS.md (after)
@@ -70,3 +70,17 @@
 Keeping a skill in the central library does not authorize global installation. Global skill directories are for broadly useful development capabilities. Psychology, history/geography, reading/learning, content operations, and other specialist workflows stay in `~/.skills-manager/skills/` unless needed by an identified project or task.
 
 For an explicitly named skill or a relevant specialist task, read only the matching central-library `SKILL.md` and necessary supporting files. The withdrawn inventory is in `~/.skills-manager/optional-skills.md`. Do not scan or preload the entire central library, reinstall these entries globally, or treat preservation as authorization for global deployment. Use project-local skill links only for the user's selected project. Existing project-local and plugin-managed skills retain their own scope.
+
+## 仓库收尾与交付约定
+
+遵循用户确认的长期收尾准则：
+
+1. **默认及时提交与推送有效工作**：对已验证的有效成果，日常收尾应及时完成本地提交并推送到既有远端仓库，无需反复询问 commit/push 许可。后续若有显式只读、禁止推送或特定范围指令，以最新明确指令优先。
+2. **收尾责任覆盖全仓有效遗留**：收尾责任覆盖仓库当前积累的所有未提交变动，包括其他 Agent 或此前任务留下的成果。先理解、协调、检查，再整合交付；严禁未经核实直接 `git add -A`，也不得因“非本人修改”直接跳过或忽略。
+3. **一个主 Agent 串行整合与进行中改动保护**：由当前主 Agent 统筹理解并串行整合。严禁覆盖或盲目丢弃仍在进行中的工作；应结合既有任务记录（如 `plans/` 下的 task_plan/findings/progress）和实际文件变动进行协调，不得武断猜测为废弃。
+4. **与变动成比例的严格验证**：提交交付前须执行成比例的必要验证（文档相对链接与 diff 检查、相关代码的必要测试）；不为简单文档编写镜像实现的冗余测试；进程退出码 0 或部分输出不等于真实应用验收通过。
+5. **无法交付时的可恢复交接**：对证据不足、测试未过、范围过大暂时无法完整审查或仍在进行中的模块，应保留改动并在任务进度中详细说明具体阻碍、保留原因，明确接续 owner（如根 Codex）及最短验收入口，留下清晰可恢复的交接，不得以“与本任务无关”推脱。
+6. **安全底线与权限边界**：
+   - 严禁 force-push、删除分支或仓库、修改仓库可见性。
+   - 严禁将密钥、凭据、Token、`.env`、本地会话状态或运行时日志提交入库。
+   - 默认提交推送授权不因“GitHub 账户切换不等于 push 授权”而被否定，但必须在 `qiaoqiao2521` 既有目标仓库内操作，保持命令级环境与凭据隔离，不修改 GitHub 账户配置。
```

## 2. 全局协作入口与指针验证

各 CLI 的全局配置指针核验结果：

1. **Codex**: `/home/muqiao/.codex/AGENTS.md` -> `/home/muqiao/.agents/AGENTS.md`（原有有效软链接）
2. **Claude**: `/home/muqiao/.claude/CLAUDE.md`（内容包含 `@../.agents/AGENTS.md` 引用）
3. **用户根目录**: `/home/muqiao/AGENTS.md`（指向 `~/.agents/AGENTS.md` 的说明指针）
4. **AGY (Antigravity CLI)**:
   - 依据 AGY 内置 Customization Rules 指南，全局配置根位于 `~/.gemini/config/`，支持 `rules/*.md` 及 `AGENTS.md`。此前 `~/.gemini/config/rules/` 不存在。
   - 本次创建软链接：`/home/muqiao/.gemini/config/rules/AGENTS.md -> /home/muqiao/.agents/AGENTS.md`。
   - SHA256 与共享源文件严格一致（`fb1d564d8380a9fa66abf59a121e7f5b63dd336068f26fab0880058f6f6a9166`），无文本重复复制，保持全局唯一权威正文。
   - 遵照用户要求，不主动在此会话内使用当前模型开子会话伪装外部加载，交由根 Codex 在轻量新 AGY 会话中进行独立端到端读取验证。

## 3. GitHub 身份与目标仓库核验

依据全局规范要求的命令隔离环境进行验证：

```bash
env -u GH_TOKEN -u GITHUB_TOKEN \
  -u GH_ENTERPRISE_TOKEN -u GITHUB_ENTERPRISE_TOKEN \
  GH_CONFIG_DIR=/home/muqiao/.config/gh-migration-qiaoqiao2521 \
  /home/muqiao/.local/bin/gh api user --jq '{login,id}'
```

- **验证用户**: `qiaoqiao2521` (ID `238822818`)
- **Git Remote**: `origin = https://github.com/qiaoqiao2521/ControlMesh.git` (fetch & push)
- **仓库归属**: `owner.login = qiaoqiao2521`, `visibility = PUBLIC`, `isFork = false`
- **提交作者**: 使用明确配置 `qiaoqiao2521 <238822818+qiaoqiao2521@users.noreply.github.com>`，不产生未授权账户变更。

## 4. ControlMesh 仓库积累修改分类盘点

基线状态记录：
- **基线 HEAD**: `dae4d6cc93fdb0fa5723cd718a5936bbfbbd1626`
- **基线状态清单**: `/home/muqiao/Documents/Codex/2026-09-27/t/work/cm-closeout-policy-20260930/baseline-status.txt`

逐项审查与分类：

### 分类 A：有效并本次交付 (Effective & Delivered)
- `plans/repository-closeout-policy/`:
  - `task_plan.md`、`findings.md`、`progress.md`
  - 范围：全局收尾约定落地、补丁记录、各 CLI 指针验证、全仓累积变动分类盘点及交接。
  - 验证：文档完整、精确 patch 校验、指针软链可解析。

### 分类 B：仍在进行中的工作 (In Progress / Active Canary)
- `plans/paperclip-feishu-canary/`:
  - 包含 `task_plan.md`、`findings.md`、`progress.md` 及 `evidence/`（兼容版补丁与测试 JSON）。
  - 实际状态：2026-09-30 开展的 Paperclip 飞书连接器兼容改造及 greenrise 服务器替换金丝雀测试。
  - 保留原因：其自身 `progress.md` 明确记录“尚未接管旧CM入口，原CM保留... 试验结束后候选服务停止并禁用自启... 无提交或推送... 先修正选定服务器CLI的实际非交互工具权限/提供商可用性，再重放一条真实交付”。属于活跃在测的 WIP 阶段，不可武断猜测为废弃，亦未达到独立封板交付条件。
  - 接续 Owner：根 Codex。

### 分类 C：证据不足 / 待完整审查的旧大块候选项 (Legacy Uncommitted Candidate)
- **无头 Orca 桥接候选实现与测试**：
  - 源码：`controlmesh/cli_commands/orca.py`、`controlmesh/orca_bridge/` (15 个 Python 模块)
  - 追踪修改：`controlmesh/__main__.py`（添加 orca 子命令）、`controlmesh/cli_commands/status.py`（添加帮助提示）
  - 测试：`tests/orca_bridge/` (19 个模块)、`tests/golden/fixtures/orca/` (6 个文件)、`tests/golden/runners/`、`tests/golden/test_orca_*`
  - 脚本与规划：`scripts/orca_*` (5 个探针/启动脚本)、`plans/cm-orca-headless-bridge-v0/` (5 个文档)
  - 实际验证结果：使用 `./.venv/bin/pytest tests/orca_bridge/ tests/golden/test_orca_*.py` 运行 1084 项测试，结果 **1083 passed, 1 failed**（`tests/orca_bridge/test_journal.py::test_reject_nonprivate_or_nondedicated_directory_without_chmod` 因环境 umask 0077 导致 mkdir 0755 实际权限为 0700 未抛出 ValueError 失败）。全仓 6850 项完整测试未跑。
  - 架构与决策状态：2026-09-30 用户已确认 CM 后续基于 Paperclip 改进，Orca 已被取代不再是默认未来底座；且已提交的 `docs/orca-bridge-status.md` 明确约定“Detailed candidate implementation and server evidence remain local and are excluded from this documentation-only publication”。
  - 保留原因：属于典型的“旧大块暂时无法完整审查”内容。保留原貌，不修改、不删除、不强行盲加。
  - 接续 Owner：根 Codex。
  - 最短验收入口：`./.venv/bin/pytest tests/orca_bridge/ tests/golden/test_orca_*.py`。

### 分类 D：历史方向记录与任务存档 (Historical Records & Planning)
- `plans/paperclip-based-cm/`: 2026-09-30 记录用户确认 CM 基于 Paperclip 改进的决议与 CLI 派发实测数据。
- `plans/bounded-delivery/`: 2026-09-14 历史 TS 分批交付卡片。
- `plans/runtime-convergence/delegation/`: 2026-09-13 历史 AGY cron 规范派发记录（4 个 md 文件）。
- 追踪文档修改：`AGENTS.md`、`PROJECT.md`、`docs/ARCHITECTURE.md`、`docs/DECISIONS.md`、`plans/README.md`、`plans/runtime-convergence/...`、`plans/terminal-product-v1/...`。
  - 经 `git diff --check` 校验全部合规。
  - 保留原因：这些修改与 `plans/README.md` 中指向的 owner-local 计划目录（如 `paperclip-feishu-canary`、`cm-orca-headless-bridge-v0`）存在链接关联；在相关计划完成收尾与发布边界裁定前，保持工作区一致，避免发布断链。
  - 接续 Owner：根 Codex。
