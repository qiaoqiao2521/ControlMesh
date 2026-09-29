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
   - **独立加载核验结果**：根 Codex 另起新 AGY 会话（会话 ID `d0475daf-fb7c-4309-9e9d-50071709f256`，记录于 `autoload.json`）完成端到端独立核查：新进程自动成功加载 `/home/muqiao/.gemini/config/rules/AGENTS.md`（§ 仓库收尾与交付约定），读取耗时 6.42 秒，状态 SUCCESS。CM 首次状态回写 422 系 agent-authored in_review 缺少有效 review 路径引起，非 AGY 执行或规则加载失败。

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

## 4. ControlMesh 仓库积累修改分类盘点与纠正

基线状态记录：
- **基线 HEAD**: `dae4d6cc93fdb0fa5723cd718a5936bbfbbd1626`
- **基线状态清单**: `/home/muqiao/Documents/Codex/2026-09-27/t/work/cm-closeout-policy-20260930/baseline-status.txt`

逐项审查与分类：

### 分类 A：成熟文档与有效成果交付 (Delivered Documents & Specifications)
1. `plans/repository-closeout-policy/`:
   - `task_plan.md`、`findings.md`、`progress.md`
   - 全局收尾约定落地、补丁记录、各 CLI 指针验证、全仓累积变动分类盘点及交接。
2. `plans/paperclip-based-cm/`:
   - `task_plan.md`、`findings.md`、`progress.md`
   - 2026-09-30 确认 CM 后续基于 Paperclip 改进的方向决议，以及真实的 CLI 协调（AGY/CBC/ZCode 派发、事件唤醒与审批）实测数据。
3. `plans/paperclip-feishu-canary/`:
   - `task_plan.md`、`findings.md`、`progress.md` 及 `evidence/`（`CM-COMPAT.md`、`compat-build.json`、`compat-quiet-test.json`、`compat-rpc-tests.json`、`compat-tests.json`、`plugin-candidate.patch`）。
   - **审查说明**：已逐项审查公开内容，排除 runtime 日志、本地会话状态与凭据；补丁为可发布源代码，JSON 为测试与构建摘要。
   - **状态纠正**：实验已明确结束，活动运行数为 0，候选服务已 stop + disable，旧 CM 一直正常运行。后续接管所需的公网 HTTPS 反代、CLI 权限与 12 项 cron 迁移属于未来生产接管的前提条件，不构成已完成的本地飞书兼容改造与服务器资源测量实验报告入库的阻碍。只读证据充足，无须重开服务器实验。
4. `plans/bounded-delivery/`:
   - `task_plan.md`、`findings.md`、`progress.md`
   - 2026-09-14 历史单卡分批交付计划与出口设计，完整成熟文档。
5. **已审阅的追踪文档与计划更新**：
   - `PROJECT.md`（修正 Current Priority 过时的不提交描述，链接更新）、`AGENTS.md`（明确本地飞书文本闭环通过、生产迁移未通过）、`docs/ARCHITECTURE.md`（修正架构开头与 Orca 为历史候选）、`docs/DECISIONS.md`（链接修正）、`docs/orca-bridge-status.md`（确认 Orca 已被 Paperclip 取代）、`plans/README.md`（更新当前工作索引与金丝雀报告）、`plans/runtime-convergence/task_plan.md`、`progress.md`、`delegation/README.md`、`plans/terminal-product-v1/task_plan.md`。
   - 所有文档链接已定向至已发布文档或本地代码路径，避免依赖未发布计划；`git diff --check` 全部通过。

### 分类 B：证据不足 / 待完整审查的旧大块候选项 (Legacy Candidates Retained Locally)
- **无头 Orca 桥接实现与测试**：
  - 源码：`controlmesh/cli_commands/orca.py`、`controlmesh/orca_bridge/` (15 个 Python 模块)
  - 追踪修改：`controlmesh/__main__.py`、`controlmesh/cli_commands/status.py`
  - 测试：`tests/orca_bridge/` (19 个模块)、`tests/golden/fixtures/orca/` (6 个文件)、`tests/golden/runners/`、`tests/golden/test_orca_*`
  - 脚本与规划：`scripts/orca_*` (5 个探针/启动脚本)、`plans/cm-orca-headless-bridge-v0/` (5 个文档)
  - **真实保留阻碍**：
    1) 2026-09-30 用户已确认 CM 改向 Paperclip，Orca 默认优先级已被取代；
    2) 已提交的 `docs/orca-bridge-status.md` 明确约定 detailed candidate implementation 本地保留不发布；
    3) 测试集中 1 项失败（`test_reject_nonprivate_or_nondedicated_directory_without_chmod`）系因执行环境 umask 0077 导致 fixture 创建目录实际为 0700，属测试 fixture 受环境影响而非产品故障；本次遵照指示不修 Orca、不跑 6850 全套。
  - 处理方式：完整保留原貌，不修改、不删除、不入库。
  - 接续 Owner：根 Codex。
  - 最短验收入口：`./.venv/bin/pytest tests/orca_bridge/ tests/golden/test_orca_*.py`。

### 分类 C：未审查提议保留 (Unreviewed Proposals Retained Locally)
- `plans/runtime-convergence/delegation/`: `agy-cron-batch-1-result.md`、`agy-result.md`、`agy-review-1.md`、`cron-port-spec.md`。
- **保留阻碍**：属于未审查/未被主 Agent 最终接受的 cron 移植方案，状态明确为 primary acceptance pending，不能称为已验收，原貌保留在本地工作区。
- 接续 Owner：根 Codex。
