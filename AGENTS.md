# Project Instructions

## 当前任务边界（2026-11-26）

CM 提供一个轻量执行与验收入口：`cm run` 运行调用方明确选定的命令，记录实际结果，执行显式检查，核对产物并给出接续建议。主 Agent 负责理解任务、选择执行者、回读产物，以及按已有授权修复和交付。

记忆能力直接归 [AgentTraceMesh 插件](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md)。CM 不维护记忆存储、召回、上下文注入或记忆回执转发；不要恢复 `cm context`、`cm run --context` 或另建适配层。

默认使用当前宿主。只有任务需要时才使用其他 CLI 或生成交接包。旧 Python / TS Runtime、Paperclip、Orca 和旧平台说明已经按用户要求退出当前源码；需要追溯时读取 [清理前基线](https://github.com/qiaoqiao2521/ControlMesh/tree/851d78b8989d07281d0082a5105f878a99f589c8)，不要因历史待办重新建立这些平台。

## 渐进读取

先读 `PROJECT.md`，再读当前任务的 `plans/<task>/task_plan.md`、`findings.md` 和 `progress.md`（存在时）。简单任务无需新建计划目录。

按问题选读：

- 执行、状态和接续：`docs/run.md`
- 模块职责：`docs/ARCHITECTURE.md`
- 已确认取舍：`docs/DECISIONS.md`
- 外部 CLI：`docs/agent-link-subagents.md`
- 真正交接：`docs/workflows/small-change.md`
- 外部后台完成通知：`docs/codex-callback.md`

`docs/README.md` 只是索引，不是必读清单。历史对话和摘要提供线索，当前代码与已确认项目记录决定当前事实。

## 做完任务

1. 动手前检查 `git status --short` 和有关源码，保留现有成果，协调仍在进行的修改。
2. 写清目标、必要输入、修改范围和可观察的验收要求，复用已有任务记录。
3. 优先使用宿主原生执行与子 Agent；并行只用于可以独立处理的部分。
4. 有子任务时主 Agent 回读真实产物和检查结果。退出 0、完成通知、交接有效和 worker 自述都不代替业务验收。
5. 失败时根据实际错误继续处理可执行部分。`next_action` 只给建议，不新增审批环节、不扩大已有授权，也不要求机械遵从。
6. 遵循用户当前会话已有的提交和推送授权，核对相关 diff、远端基线及必要检查后交付。不要覆盖正在进行的工作；确有阻碍时记录具体原因和接续入口。

`cm run --task` 只记录任务身份，不自动把文件内容传给 CLI。调用方负责明确命令参数。`--artifact` 是验收清单，不是沙箱。不要把本机命令测试描述为真实模型、服务器或通知通道验收。

## 外部 CLI 选择

- 默认外部候选只有 Qoder；使用前按任务核对当前可用性，历史可用不保证今天可用。
- AGY 只在用户明确点名时人工前台使用；不自动探测、不 spawn、不作为后台或降级候选。
- CBC 仅显式指定；ZCode 使用已配置的 edit 模式；DSH 派发暂停。
- 需要额度探测时同批最多一次，沿用 `scripts/agent_quota_check.py`。外部通道已知不可用时直接使用内置能力，不为探测消耗模型请求。
- 外部作业可能已启动时，先做一次针对性确认，避免重复写入。完成通知只保留一个 owner；短同步调用与后台回调分别验收。

具体参数见 [agent-link](docs/agent-link-subagents.md) 和 [任务材料](skills/cli-dispatch-handoff/references/task-and-handoff.md)。工具、权限、登录、模型和原生会话由各宿主维护。acpx / 统一 ACP、hcom 平台化接入、Magpie 模型统筹不重新进入默认队列。

## 复用与流程成本

优先使用已有工具、已有项目检查和普通文件，只为真实缺口补最小实现。不要新增调度数据库、长期服务、统一认证、额度路由或通用记忆平台。普通小任务不强制交接包、知识写回、多角色会审或额外审批。

SpecMesh 保存项目当前意图和进度，TraceMesh 提供历史证据并独立维护记忆插件，CapMesh 保存能力取舍。可选 `cm-workflow` 保留来源与新鲜度检查；材料有效不等于任务完成。可选 `cm-closeout` 只同步明确配置的已提交段落。

知识库只在与当前任务有关时按已有本机配置选读；不可用时继续当前任务，不默认扫描全库，不为每个任务安装新服务。

## 修改、验证与记录

- 先读拥有行为的模块和测试；验证范围与改动及剩余风险相称。
- 标准库执行入口使用 `python3 -B -S` 验证；外部 CLI、callback 和独立 SpecMesh 分别记录依赖与验收边界。
- 没有新错误或必须满足的门槛时，不反复扩大测试。
- 项目方向变更写 `PROJECT.md`，职责变更写 `docs/ARCHITECTURE.md`，关键取舍写 `docs/DECISIONS.md`；一次任务事实留在原计划。
- 不提交凭据、`.env`、登录态、个人记忆、运行报告、日志、缓存、依赖或构建输出。
- 源码退役不操作服务器，不移除运行数据，也不证明生产迁移完成。若另有部署任务，以该任务的明确授权和实际状态为准。
