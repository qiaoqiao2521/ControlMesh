# agent-link-mcp：本机 CLI 子任务

用户于 2026-10-24 选定 [agent-link-mcp](https://github.com/mikusnuz/agent-link-mcp)。本次只接入 CLI 子任务调用，不改变 CM 的默认单 Harness 方向，也不恢复 ACP 或跨 Harness 管理平台。

## 已安装内容

- 上游包 `agent-link-mcp@0.5.3`，MIT，Node >=20。
- 一个名为 `agent-link` 的 Codex stdio MCP 服务，工具超时 600 秒。
- 本机 `~/.agent-link/config.json` 配置 `agy`、`qoder`、`cbc`。
- 使用已有 CLI 自身的登录、默认模型和网络配置。没有新认证、模型代理或常驻调度服务。
- 使用 Node 与包入口的绝对路径，减少桌面启动环境与终端 PATH 差异。

本机入口可用 `codex mcp get agent-link --json` 查询。CLI 本身仍由各自的安装方式维护。

## 如何调用

在 Codex 中明确指定工具、CLI、任务和工作目录：

> 调用 agent-link 的 spawn_agent，agent=qoder，cwd=这个项目的绝对路径。让它检查指定文件并返回结果，不再派生其他 Agent。

相应的工具参数：

```json
{
  "agent": "qoder",
  "task": "Read the requested file and report the findings. Do not modify files.",
  "cwd": "/absolute/path/to/project",
  "timeoutMs": 120000,
  "retry": false
}
```

将 `agent` 改为 `agy` 或 `cbc` 可使用另外两个已配置 CLI。`cbc` 是本机 CodeBuddy Code 的实际入口；没有创建 `bcb` 别名。

上游还提供 `spawn_agents`、`reply`、`kill_agent`、`list_agents`、`get_status`。`reply` 会重新启动 CLI，并传入记录的对话；它不是 CLI 原生会话恢复。服务重启后内存中的对话记录不保留。

## 当前验收

2026-10-24，使用 MCP SDK 连接已安装的上游 stdio 服务：

- 握手成功，枚举到六个工具。
- `list_agents` 确认 `agy`、`qoder`、`cbc` 的绝对路径可执行。
- 一次 `spawn_agent(agent=qoder)` 读取本地文件，返回文件中的随机标记和正确和数 96；独立回读结果通过。
- AGY、CodeBuddy 只完成配置与可执行性检查，尚未实测任务。
- Codex 配置读回为 enabled；当前 App 对话的新 MCP 工具加载与实际选择尚未确认。

该结果证明同步 MCP 调用可用，不代表原生 Codex 子 Agent 生命周期或 App 直接调用已验收。

## 后台接续边界

上游同步工具会等待 CLI 返回结果，没有内置原会话 `codex queue` 回调。若以后增加独立后台派发，完成事件必须按现有约定经 native queue 回原线程。

本次旧控制 socket 返回 ENOENT，未设置共享控制通道。没有启动替代 daemon、重开 App、发送 queue 消息或新增 callback。异步完成接续保持未验收，不能用同步测试代替。

## 继续与移除

- 下一次在 App 对话中按上面的明确指令调用，确认新 MCP 工具已实际加载。
- 若未加载，先检查 App 的 MCP 连接状态；不因包已安装就判断触发已修复。
- 移除 Codex 注册：`codex mcp remove agent-link`。
- 移除 npm 包：`npm uninstall -g agent-link-mcp`。
- 独立配置文件可按需保留或人工编辑。

运行回执保存在本机私有状态目录，不提交到仓库。任务进度见[接入计划](../plans/agent-link-subagent-smoke/task_plan.md)。
