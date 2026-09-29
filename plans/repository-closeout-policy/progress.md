# Progress — 仓库收尾与交付规范实施

## Current
AGY 实施、入口核验与有效工作交付完成。全局共享规范已更新，AGY 全局规则软链接已建立；CM 仓库所有未提交工作已全面盘点分类；本任务成果已提交并推送到远端；保留的未完成/未审查遗留已明确记录阻碍并交接给根 Codex。

## Done
1. **全局共享规范修订**：
   - 目标文件：`/home/muqiao/.agents/AGENTS.md`（普通文件，不在 Git 追踪）。
   - 修订前 SHA256：`e7d0d6c14fb061574787ea52c7dd72d08ed4ac45d1dda8610e0508ee7d626fe2`。
   - 修订后 SHA256：`fb1d564d8380a9fa66abf59a121e7f5b63dd336068f26fab0880058f6f6a9166`。
   - 新增《仓库收尾与交付约定》小节，完整覆盖及时提交推送有效工作、全仓有效遗留覆盖、单主 Agent 串行整合、进行中改动保护、成比例验证、无法交付时的可恢复交接、日常收尾无需反复询问、后续明确指令优先，以及安全底线。
   - 保留全部既有规则段落，未改动任何其他配置。
2. **全局协作入口与指针核验**：
   - Codex 指针：`/home/muqiao/.codex/AGENTS.md` -> `/home/muqiao/.agents/AGENTS.md`（有效软链接）。
   - Claude 指针：`/home/muqiao/.claude/CLAUDE.md`（内容包含 `@../.agents/AGENTS.md`）。
   - 用户根指针：`/home/muqiao/AGENTS.md`（有效指向 `~/.agents/AGENTS.md`）。
   - AGY 全局规则接入：依据内置 Rules 指南，创建软链接 `/home/muqiao/.gemini/config/rules/AGENTS.md -> /home/muqiao/.agents/AGENTS.md`。核验其解析路径与 SHA256 严格一致，保持单一本机正文。
3. **GitHub 身份与仓库所有权核实**：
   - 使用隔离环境 `GH_CONFIG_DIR=/home/muqiao/.config/gh-migration-qiaoqiao2521`。
   - 验证身份为 `qiaoqiao2521` (ID `238822818`)。
   - 验证目标仓库 `qiaoqiao2521/ControlMesh`，所有者为 `qiaoqiao2521`，公开仓库，fetch/push URL 一致。
4. **ControlMesh 仓库未提交变动全面盘点与分类**：
   - 基线 HEAD：`dae4d6cc93fdb0fa5723cd718a5936bbfbbd1626`。
   - 详见 `findings.md` 分类清单。
   - 明确本次交付范围：`plans/repository-closeout-policy/`。
5. **必要测试验证**：
   - 运行 Orca 桥接与黄金测试集 1084 项：1083 passed, 1 failed（因 umask 0077 导致 journal 权限断言不匹配，记录为不提交 Orca 代码的依据之一）。

## Handover & Retained Legacy (移交根 Codex 独立审批与接续)

以下未提交项目已完整保留在工作区，未被修改、覆盖或删除：

1. **进行中金丝雀 (WIP)**：`plans/paperclip-feishu-canary/`
   - 具体阻碍：greenrise 部署与资源测量已完成，但原 CM 仍驻留，Telegram 缺少 HTTPS 反代，CLI 权限尚未修齐，尚未接管旧入口，处于活跃实验中间态。
   - 接续 Owner：根 Codex。
   - 最短验收入口：`plans/paperclip-feishu-canary/progress.md`。
2. **旧大块未审查候选**：Orca 桥接实现与测试
   - 涉及路径：`controlmesh/orca_bridge/`、`controlmesh/cli_commands/orca.py`、`tests/orca_bridge/`、`scripts/orca_*`、`plans/cm-orca-headless-bridge-v0/`、`controlmesh/__main__.py`、`controlmesh/cli_commands/status.py`。
   - 具体阻碍：
     1) 2026-09-30 用户已确认 CM 改向 Paperclip，Orca 默认优先级已被取代；
     2) 已提交的 `docs/orca-bridge-status.md` 明确约定 detailed implementation 本地保留不发布；
     3) 运行 `./.venv/bin/pytest tests/orca_bridge/ tests/golden/test_orca_*.py` 存在 1 项因 umask 导致的测试失败；全仓 6850 项测试未全跑。
   - 接续 Owner：根 Codex。
   - 最短验收入口：`./.venv/bin/pytest tests/orca_bridge/ tests/golden/test_orca_*.py`。
3. **历史方向与文档同步**：
   - 涉及路径：`plans/paperclip-based-cm/`、`plans/bounded-delivery/`、`plans/runtime-convergence/delegation/` 以及已暂存的文档更新 (`PROJECT.md`、`AGENTS.md` 等)。
   - 具体阻碍：与未发布的本地候选计划保持一致，避免独立推送引起文档间相对链接断裂。
   - 接续 Owner：根 Codex。
