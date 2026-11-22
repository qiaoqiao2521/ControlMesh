# ControlMesh

**CM 把实际开发经验整理为多个 Harness 都能使用的工作流。** 从明确需求、按需查证据，到实施、独立验收和交付，复用现有 Mesh 与项目文件。各 Harness 负责自己的工具、权限和执行，CM 只补工作流里已经出现的具体缺口。

## 当前怎么用

| 需要 | 复用方式 | 验收范围 |
| --- | --- | --- |
| 完成一项可核验的小改动 | [带证据的小改动交付](docs/workflows/small-change.md)；需要交接时使用 `python3 -S -m controlmesh.workflow prepare\|check` | 本轮结果与限制见[实际进度](plans/workflow-small-change-20261122/progress.md) |
| 宿主内多 Agent 协作 | 宿主原生子 Agent、线程与任务工具 | 按具体任务验收 |
| 调用另一个 CLI 做子任务 | 可选 [agent-link-mcp](docs/agent-link-subagents.md)，沿用 CLI 自己的配置 | 各 CLI 的历史验收见原计划；当前可用性按任务核对 |
| 后台任务完成后继续 | 发起端原生完成通知；Codex 外部后台回传使用 [native queue](docs/codex-callback.md) | MCode idle 与本机 queue 闭环有历史验收；当前通道需按任务核对 |
| 个人陪伴记忆 | 可选 [DSH Companion Memory](plugins/dsh-companion-memory/README.md) | 插件行为已测试；真实模型长期记忆质量待验证 |

在已配置 agent-link 的 Codex 中，可以直接交代：

> 用 agent-link 的 spawn_agent，把这个目录的指定文件交给 qoder 审查。只读文件，返回发现和依据，由主 Agent 核验。

传入明确的 `agent`、`task`、`cwd`。多个独立子任务可用 `spawn_agents`。具体配置、版本和限制见[使用说明](docs/agent-link-subagents.md)，本轮状态见[进度](plans/agent-link-subagent-smoke/progress.md)。安装旧 CM Python 包不是这条调用路径的前提。

## 分工与边界

- **CM 工作流**：保存可复用的步骤、输入依据、范围、验收和接续方法；普通任务沿用现有记录。
- **主 Agent**：理解目标、按需选择执行者、给必要上下文、整合并独立验收真实结果。
- **各 CLI／Harness**：维护自身登录、模型、代理、工具、权限、上下文和原生会话。
- **社区工具与薄适配**：连接任务调用、产物交接与适用的完成通道。同步工具返回和异步 queue 分别验收。
- **项目连续性**：SpecMesh 保存当前项目意图、进度与代码职责，AgentTraceMesh 保存历史证据，CapMesh 记录能力取舍。历史摘要不自动成为当前事实；旧 CM 通用记忆退出默认 Mesh，陪伴插件独立可选。

需要时仍可把其他 CLI 当子 Agent 使用。统一认证、额度路由、模型代理、会话同步和调度数据库不属于本轮工作流；acpx／统一 ACP、hcom 平台化接入和 Magpie 模型统筹保持退出默认计划。切换执行者不保证解决额度，也不迁移原生会话。

首条流程使用普通 Markdown 和现有计划；换执行者或跨会话时，可通过薄命令复用独立 SpecMesh 的材料生成与消费前核验。无需新索引或后台服务。后续知识炼油、CapMesh 加固与选择性记忆都从真实任务中提炼，按减少协调和维护负担判断价值，见[最新决策](docs/DECISIONS.md#2026-11-22--把开发工作流作为-cm-核心)。

## 保留的实现

仓库仍保存旧 Python CM 的终端、任务、记忆、消息与调度代码，以及 TS SDK／只读面板、Orca 候选和 Paperclip 适配。这些用于已有部署、历史追溯与按需复用，不是当前默认建设清单。方向更新不代表旧服务已迁移或停用。

- 既有 Paperclip 运维：[总览](plans/paperclip-based-cm/progress.md)、[436 运行说明](docs/paperclip-436.md)。
- 旧 Python CM 安装与运行：[安装说明](docs/installation.md)、[终端](docs/terminal.md)、[只读 Alpha](docs/read-only-alpha.md)。
- 当前项目方向：[PROJECT.md](PROJECT.md)。
- 系统分工：[架构](docs/ARCHITECTURE.md)；历史取舍：[决策](docs/DECISIONS.md)。
- 其他模块：[文档索引](docs/README.md)；贡献者先读 [AGENTS.md](AGENTS.md)。

## License

MIT. See [LICENSE](LICENSE). Reused components retain their own license notices.
