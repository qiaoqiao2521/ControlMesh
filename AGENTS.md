# Project Instructions

## Start Here

First read:

1. `PROJECT.md`

Then read only what the task requires:

- Architecture and ownership boundaries → `docs/ARCHITECTURE.md`
- Historical decisions and rejected directions → `docs/DECISIONS.md`
- Active substantial work → the relevant `plans/<task>/` directory

Do not load unrelated documentation by default. `docs/README.md` is a catalog, not a
required reading list.

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
- Python still owns existing production paths. As confirmed on 2026-09-30, the next CM is
  based on Paperclip; start at `plans/paperclip-based-cm/`. The Orca bridge and full-TypeScript
  candidate are retained evidence, not the default execution queue. The local CLI
  dispatch/idle/event-wake/review path and local Feishu text closed-loop are verified; production migration is not.
  Reuse upstream lifecycle ownership; do not add a parallel scheduler or migrate tasks from
  a plan alone. Existing JSON Schema contracts and private-runtime boundaries remain.
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
