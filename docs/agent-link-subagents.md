# agent-link：调用已有 CLI 子任务

优先使用当前宿主的原生子 Agent。任务确实需要其他已配置 CLI 时，可选用 [agent-link-mcp](https://github.com/mikusnuz/agent-link-mcp) 做短同步调用；它不属于 CM 核心安装依赖。

用户于 2026-10-24 选择该工具。历史安装记录是 `agent-link-mcp@0.5.3`、Node >=20、Codex stdio MCP 服务；今天是否已加载、CLI 是否可执行和调用是否有效，应以本轮环境为准，不从历史记录推定。

## 当前派发范围

| CLI | 选择规则 |
| --- | --- |
| Qoder | 默认外部候选；本次可用性单独检查 |
| ZCode | 按任务选用，沿用 edit 配置，不进入默认候选 |
| CBC | 只在显式指定时使用；历史额度失败不等于永久禁用 |
| AGY | 仅用户显式点名时人工前台使用；不自动探测、不 spawn、不作为后台或降级候选 |
| DSH | CLI 派发暂停；独立陪伴插件按其自身范围使用 |

模型、登录、网络、权限与原生会话由各 CLI 维护。不要自行添加跳过权限参数、创建统一认证或为了接口一致而恢复 ACP 平台。

需要检查外部候选时，在 checkout 根目录按本批任务使用一次：

```sh
python3 scripts/agent_quota_check.py --pick
python3 scripts/agent_quota_check.py qoder
```

以上是两种可选调用方式，不需连续执行。默认候选仅 Qoder。脚本沿用现有登录发出短模型请求，属于可用性探测，不是精确余额查询。

`degraded`、`unknown`、`timeout` 不能当成成功。同批不循环探测；没有就绪外部通道时使用宿主原生能力。CBC 只有显式指定时检查。AGY 的历史兼容参数不是自动调用入口。

## 短同步调用

将明确的 CLI、任务和工作目录传给 agent-link，例如：

```json
{
  "agent": "qoder",
  "task": "读取指定文件，返回发现与依据；不修改文件，不派生其他 Agent。",
  "cwd": "/absolute/project",
  "timeoutMs": 120000,
  "retry": false
}
```

已配置的 profile 使用自己原来的命令和参数，CM 不维护另一份凭据或模型映射。可用 `codex mcp get agent-link --json` 核对现有服务；该命令只适用于已安装的相应宿主。

上游还提供 `spawn_agents`、`reply`、`kill_agent`、`list_agents`、`get_status`。历史版本的 `reply` 是新起 CLI 并重放已记录对话，不等于原生会话恢复；服务重启后的内存对话也不自动保留。

## 实际结果与失败接续

主 Agent 检查真实产物和有意义的正文。可执行文件存在、`available=true`、进程退出 0 或空 `done` 都不证明任务完成。历史测试曾发现 CBC 额度耗尽但退出 0，正说明需要独立检查。

已有明确命令且需要保存检查与产物记录时，可使用 [`cm run`](run.md)。任务文件必须通过该 CLI 的原有输入方式传入，`cm run --task` 本身不会喂给模型。报告给出建议，宿主按原任务与已有授权继续修复。

需要外部后台作业时，优先宿主原生后台机制；只有通道已就绪时才选 [独立 callback](codex-callback.md)。agent-link 同步返回不提供原线程 queue 回调，不能用一次同步成功证明后台恢复可用。

外部作业可能已启动时先核对一次，避免重复执行。回调失败保留原任务结果，不自动重跑收费任务；通道不可用时由内置 Agent 或主 Agent 接手可执行部分。

## 历史验收

2026-10-24/25 已有 Qoder 同步读取文件和真实文档审查、ZCode 指定文件修改的独立核验。AGY、DSH 当日曾有成功调用；CBC 当日受额度阻断。这些是带日期的历史事实，当前选择规则以上表为准。

详细证据见 [历史进度](../plans/agent-link-subagent-smoke/progress.md)。它不覆盖当前 App 连接、所有 CLI、后台唤醒、取消或原生会话恢复。

任务材料和已有 hcom 作业处理见 [任务与交接索引](../skills/cli-dispatch-handoff/references/task-and-handoff.md)；沿用已有工具，不再建设 hcom 管理平台。
