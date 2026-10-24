# ControlMesh

**CM 是围绕现有 CLI 的轻量 Agent 协作与适配层。** 在原会话提出目标，主 Agent 派发子任务，收到结果后独立验收。优先使用 CLI／Harness 已有能力，只补必要的入口、交接和完成通知。

## 当前怎么用

| 需要 | 复用方式 | 验收范围 |
| --- | --- | --- |
| 宿主内多 Agent 协作 | 宿主原生子 Agent、线程与任务工具 | 按具体任务验收 |
| 调用另一个 CLI 做子任务 | [agent-link-mcp](docs/agent-link-subagents.md)，沿用 CLI 自己的配置 | Qoder、AGY、ZCode CLI、DSH 同步返回已验；CBC 当前额度耗尽，未通过 |
| 后台任务完成后继续 | 发起端原生完成通知；Codex 外部后台回传使用 [native queue](docs/codex-callback.md) | MCode idle 与本机 queue 闭环有历史验收；当前通道需按任务核对 |
| 个人陪伴记忆 | 可选 [DSH Companion Memory](plugins/dsh-companion-memory/README.md) | 插件行为已测试；真实模型长期记忆质量待验证 |

在已配置 agent-link 的 Codex 中，可以直接交代：

> 用 agent-link 的 spawn_agent，把这个目录的指定文件交给 qoder 审查。只读文件，返回发现和依据，由主 Agent 核验。

传入明确的 `agent`、`task`、`cwd`。多个独立子任务可用 `spawn_agents`。具体配置、版本和限制见[使用说明](docs/agent-link-subagents.md)，本轮状态见[进度](plans/agent-link-subagent-smoke/progress.md)。安装旧 CM Python 包不是这条调用路径的前提。

## 分工与边界

- **主 Agent**：理解目标、选择执行者、给必要上下文、整合并验收结果。
- **各 CLI／Harness**：维护自身登录、模型、代理、工具、权限、上下文和原生会话。
- **社区工具与薄适配**：连接任务调用、产物交接与适用的完成通道。同步工具返回和异步 queue 分别验收。
- **项目连续性**：SpecMesh 保存项目意图与进度，CapMesh 记录能力取舍，TraceMesh 查历史。旧 CM 通用记忆退出默认 Mesh，陪伴插件独立可选。

允许把其他 CLI 当子 Agent 使用；不扩建统一认证、模型代理、会话同步、调度数据库或多厂商 Agent Runtime 平台。acpx／统一 ACP 与 hcom 平台化接入保持停止。此前 Magpie 模型统筹试验已按 CapMesh D029 退出 Codex 主流程，不作为 CM 依赖。

新增需求先查原生能力和现成实现。只有真实任务暴露具体缺口时才做小补丁或最小适配，按减少用户协调和维护负担判断价值。完整原因见[最新决策](docs/DECISIONS.md#2026-10-25--围绕-cli-做轻量适配)。

## 保留的实现

仓库仍保存旧 Python CM 的终端、任务、记忆、消息与调度代码，以及 TS SDK／只读面板、Orca 候选和 Paperclip 适配。这些用于已有部署、历史追溯与按需复用，不是当前默认建设清单。方向更新不代表旧服务已迁移或停用。

- 既有 Paperclip 运维：[总览](plans/paperclip-based-cm/progress.md)、[436 运行说明](docs/paperclip-436.md)。
- 旧 Python CM 安装与运行：[安装说明](docs/installation.md)、[终端](docs/terminal.md)、[只读 Alpha](docs/read-only-alpha.md)。
- 当前项目方向：[PROJECT.md](PROJECT.md)。
- 系统分工：[架构](docs/ARCHITECTURE.md)；历史取舍：[决策](docs/DECISIONS.md)。
- 其他模块：[文档索引](docs/README.md)；贡献者先读 [AGENTS.md](AGENTS.md)。

## License

MIT. See [LICENSE](LICENSE). Reused components retain their own license notices.
