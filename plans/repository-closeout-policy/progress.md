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
4. **ControlMesh 仓库未提交变动全面盘点与成熟文档交付**：
   - 基线 HEAD：`dae4d6cc93fdb0fa5723cd718a5936bbfbbd1626`。
   - 详见 `findings.md` 分类清单。
   - 经审查交付范围：
     - `plans/repository-closeout-policy/`（收尾约定与规范落地）
     - `plans/paperclip-based-cm/`（Paperclip 改进方向与本地 CLI 派发实测）
     - `plans/paperclip-feishu-canary/`（飞书连接器兼容改造、去噪、greenrise 资源测量报告及 `evidence/` 下审查后的源码补丁与测试摘要；已排除 runtime 日志与凭据）
     - `plans/bounded-delivery/`（已完成的 TS 单卡分批交付计划）
     - 追踪文档与计划更新（`PROJECT.md`、`AGENTS.md`、`docs/ARCHITECTURE.md`、`docs/DECISIONS.md`、`docs/orca-bridge-status.md`、`plans/README.md`、`plans/runtime-convergence/task_plan.md`、`progress.md`、`delegation/README.md`、`plans/terminal-product-v1/task_plan.md`）。
5. **必要测试与自动加载核验**：
   - 运行 Orca 桥接与黄金测试集 1084 项：1083 passed, 1 failed（因 umask 0077 导致 journal 权限断言不匹配，表明 fixture 受环境影响，未据此断言产品故障）。
   - 根 Codex 独立新 AGY 会话规则自动加载核验通过（`autoload.json`，新会话准确识别自动加载规则，状态 SUCCESS）。
6. **提交与推送验证**：
   - 早期提交：`33af2f6`、`32074f3`。
   - 本次纠正与成熟文档交付提交并推送到 `origin/main` (`https://github.com/qiaoqiao2521/ControlMesh.git`)。

## Handover & Retained Legacy (移交根 Codex 独立审批与接续)

以下未提交项目已完整保留在本地工作区，未被修改、覆盖或删除：

1. **旧大块未审查候选**：Orca 桥接实现、测试、探针与 CLI 接线
   - 涉及路径：`controlmesh/orca_bridge/`、`controlmesh/cli_commands/orca.py`、`tests/orca_bridge/`、`tests/golden/fixtures/orca/`、`tests/golden/runners/`、`tests/golden/test_orca_*`、`scripts/orca_*`、`plans/cm-orca-headless-bridge-v0/`、`controlmesh/__main__.py`、`controlmesh/cli_commands/status.py`。
   - 真实保留阻碍：
     1) 2026-09-30 用户已确认 CM 改向 Paperclip，Orca 默认优先级已被取代；
     2) 已提交的 `docs/orca-bridge-status.md` 明确约定 detailed candidate implementation 本地保留不发布；
     3) 测试集中 1 项失败系因 umask 0077 导致 fixture 目录权限实际为 0700，表明 fixture 受环境影响，未据此断言产品缺陷；本次按指示不修 Orca、不跑 6850 全套。
   - 接续 Owner：根 Codex。
   - 最短验收入口：`./.venv/bin/pytest tests/orca_bridge/ tests/golden/test_orca_*.py`。
2. **未接受的 Cron Port 提案**：
   - 涉及路径：`plans/runtime-convergence/delegation/` 下的 `agy-cron-batch-1-result.md`、`agy-result.md`、`agy-review-1.md`、`cron-port-spec.md`。
   - 真实保留阻碍：属于未审查/未被主 Agent 最终接受的 cron 移植方案，状态明确为 primary acceptance pending，不能称为已验收，原貌保留在本地工作区。
   - 接续 Owner：根 Codex。
3. **状态与独立审批边界**：
   - CM 首次状态回写 422 来自 agent-authored in_review 缺少有效 review 路径，非 AGY 失败。
   - 外层只写 durable outcome，由根 Codex 独立进行最终审批与 review 状态修改。

## 根 Codex 最终验收

- 结论：收尾规则与 AGY 实施交付接受；保留项未被当作已验收代码。
- 独立验证：全局前后 diff/指针、新 AGY 会话自动加载；已交付补丁和测试摘要公开内容检查；变更文档链接按 Git 提交树检查，不以本地未跟踪目录存在冒充远端可访问；交付 diff 空白检查。
- 已核实 AGY 提交 `15fa17533a0a76ef287b5bfa736670dd74b6f31d` 与 GitHub main 一致。最终文档小修及本验收记录同批提交推送，具体 SHA 以此文件的 Git 历史和 CM QIA-8 结项记录为准。
- 保留 Orca 候选与未接受 cron 提案；接续 owner 为根 Codex。Cron 最短审查入口是 `plans/runtime-convergence/delegation/README.md` 的历史验收表与 `agy-review-1.md`，先核对未通过项，不自动恢复旧进程。
