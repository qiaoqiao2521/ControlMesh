# Project Instructions

## Identity — read this first

2026-10-18 当前本机方向：回到通知层。保留各 CLI 自己的调用、登录、模型配置和原生会话；复用 `codex_callback` 的完成通知、原会话 native queue 与接续回执。用户已放弃本次 acpx／统一 ACP 接入试验，不得继续要求独立 Antigravity ACP 登录、安装适配运行包或恢复三 CLI 闭环测试。
不为统一调用再引入 Paperclip、Orca 或新的调度／认证层。以下 Paperclip 说明保留已有路径和历史所有权，不是本次本机需求的强制依赖，也不授权停改已运行服务。决定与重访条件见 [2026-10-18 决策](docs/DECISIONS.md#2026-10-18--回到通知层停止-acpx统一-acp-接入)。

CM 是用户的工作流概念与适配层，实际运行底座是 [Paperclip](https://github.com/paperclipai/paperclip)，不是另一个独立运行时（2026-10-01 用户确认）。
介绍已有 Paperclip 路径时明确这一历史定位；当前本机工作以以上最新范围为准。
复用 Paperclip 的任务生命周期、派发与事件唤醒；自己的代码仅补必要的 CLI/TUI、消息入口、策略与交付适配。
不修改 Paperclip 上游核心，不重建调度器，不维护平行生命周期。
旧 Python CM、Orca 桥接和完整 TS 迁移保留为历史实现与证据，不是默认建设队列。
方向确认不等于生产迁移完成；旧生产入口保持原所有权，未经独立验收不得宣称已接管。
当前本机工作从 [回调计划](plans/codex-callback-bridge/task_plan.md) 与其进度进入；已有 Paperclip 运维才查 [Paperclip 计划](plans/paperclip-based-cm/task_plan.md)。

## Start Here

First read:

1. `PROJECT.md`

Then read only what the task requires:

- Architecture and ownership boundaries → `docs/ARCHITECTURE.md`
- Historical decisions and rejected directions → `docs/DECISIONS.md`
- Active substantial work → the relevant `plans/<task>/` directory

Do not load unrelated documentation by default. `docs/README.md` is a catalog, not a
required reading list.

## 复用与流程成本

遵循 [SpecMesh §8 的复用与流程成本](https://github.com/qiaoqiao2521/specmesh/blob/main/SPEC.md#复用与流程成本)。本机标准入口为 `~/.agents/standards/specmesh.md`；缺少该入口时按以下准则继续，不增加运行依赖。

- 新增能力前，按任务规模检查项目已有实现、已安装工具及官方或社区实现。优先使用、配置、组合或小补丁；自研仅补已核实缺口，说明无法复用的原因，未核实能力标为待核实。
- 自动化以本次有效产出为目标。允许部分自动化或人工交接；不为形式上的完整闭环增加卡片、服务、审查环节或强制知识写回。验证与变动和风险相称，保留既有身份、去重与恢复要求。
- Codex queue 接续先读当前项目入口和相关计划。派发 CM worker 时，由协调 Agent 将选定项目准则、交付物与停止条件放进已有原生任务材料；queue 不负责向外部 worker 自动加载文档。具体边界见 [回调说明](docs/codex-callback.md#准则继承与任务范围)。

## Project Memory

Conversation history is context, not project memory.

Update `PROJECT.md` only when confirmed user intent, priorities, constraints, non-goals,
or project stage changes.

Update `docs/ARCHITECTURE.md` when durable knowledge about how the system works or who owns
behavior changes.

Update `docs/DECISIONS.md` when an important choice is made that a future agent may
otherwise revisit.

For substantial work that spans multiple files, requires investigation, or may cross
sessions, maintain:

- `plans/<task>/task_plan.md`
- `plans/<task>/findings.md`
- `plans/<task>/progress.md`

Use the globally installed `planning-with-files` skill for this workflow. Keep transient
discoveries in task findings; promote only durable knowledge into project documents.

## Before Editing

- Run `git status --short` and preserve existing changes.
- Read the modules and tests that own the requested behavior.
- Determine whether the change is read-only, mutating, persisted, transport-facing, or
  provider-facing.
- Do not assume generated files are hand-written.

## Development

- Use existing development, testing, review, and validation mechanisms.
- Keep changes inside the active ownership boundary.
- Do not silently reinterpret or weaken user requirements.
- Do not rename persisted fields, task statuses, provider names, transport names, or
  relative paths without an explicit migration.
- Python still owns unmigrated production paths. The selected 436 host has switched its
  CLI and Feishu listener to Paperclip; real-message retest status and remaining boundaries
  are in `plans/436-paperclip-feishu/progress.md`. Do not restart its retired Python daemon.
  As confirmed on 2026-09-30, the next CM is
  based on Paperclip; start at `plans/paperclip-based-cm/`. The Orca bridge and full-TypeScript
  candidate are retained evidence, not the default execution queue. The local CLI
  dispatch/idle/event-wake/review path and selected Feishu text paths are verified. Fleet
  migration and later governance have dated acceptance in the current overview; each host,
  callback route and business result retains its own acceptance boundary.
  For explicitly bound local Codex tasks, follow `docs/codex-callback.md` and use
  `cm-codex-task launch` before dispatch. Reconcile original runs; never retry uncertain submissions.
  Reuse upstream lifecycle ownership; do not add a parallel scheduler or migrate tasks from
  a plan alone. Existing JSON Schema contracts and private-runtime boundaries remain.
  Keep Paperclip upstream source unmodified; CM-specific behavior belongs in a thin external
  orchestration layer using supported interfaces. The pre-execution direction review in the
  current plan is a recorded need, not an implementation queue or a closeout-CLI feature.
- Do not expose absolute artifact paths or weaken authentication/path containment.
- Do not commit secrets, credentials, `.env` files, auth profiles, caches, virtual
  environments, runtime logs, dependency directories, or local agent session state.
- Before reporting completion, run verification proportional to the change and record the
  exact result in the task progress file.

## Documentation

Keep documentation concise and linked rather than duplicated.

- Code explains implementation.
- `PROJECT.md` explains intent and current direction.
- `docs/ARCHITECTURE.md` explains the durable system map and invariants.
- `docs/DECISIONS.md` explains why important choices were made.
- Task files explain the current work only.

Do not introduce new process or infrastructure unless a real task requires it.

## 开发知识按需接入

先读本项目上下文。遇到方案取舍、重复问题或跨项目经验时，读取 `KNOWLEDGE_WORKFLOW_CONFIG` 指定的路径说明；未设置时查 `~/.config/knowledge-workflow/paths.md`，再从映射的 Obsidian `Wiki/开发知识入口.md` 选相关页，读写规则见 `Wiki/开发协作接入.md`。配置或来源不可用时跳过，不阻塞开发；不默认扫全库。

在规划与收尾 Agent 中使用该约定；CM 调度、执行所有权、任务验收和交付规则仍由本项目定义。只将选定的相关经验与来源带入任务上下文，不向所有 worker 注入全库或自动同步日记。收尾有可复用认识才由一个汇总者修订知识页；无共享文件权限的 worker 将候选留在原任务。知识引用不创建任务或扩大执行权限，普通任务不强制建卡或复测实体环境。
