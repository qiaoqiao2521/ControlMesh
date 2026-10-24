# agent-link-mcp：本机 CLI 子任务

用户于 2026-10-24 选定 [agent-link-mcp](https://github.com/mikusnuz/agent-link-mcp)，并授权主动用于合适的独立子任务。CM 优先复用宿主原生能力，需要其他 CLI 时用它调用；各 CLI 保持自有认证、模型、网络与会话，不恢复 ACP 或跨 Harness 管理平台。见[当前决定](DECISIONS.md#2026-10-25--围绕-cli-做轻量适配)。

## 已安装内容

- 上游包 `agent-link-mcp@0.5.3`，MIT，Node >=20。
- 一个名为 `agent-link` 的 Codex stdio MCP 服务，工具超时 600 秒。
- 本机 `~/.agent-link/config.json` 保留 `agy`、`zcode`、`qoder`、`cbc`；仅 DSH 按用户要求暂停，其参数单独保留，不提交仓库。
- 使用已有 CLI 自身的登录、默认模型和网络配置。没有新认证、模型代理或常驻调度服务。
- 使用 Node 与包入口的绝对路径，减少桌面启动环境与终端 PATH 差异。

本机入口可用 `codex mcp get agent-link --json` 查询。CLI 本身仍由各自的安装方式维护。

## 当前派发范围

2026-10-25 用户纠正后：

| CLI | 可否选择 | 当前依据 |
| --- | --- | --- |
| AGY | 可以 | 此前真实文件任务通过；本次未重复调用 |
| ZCode CLI | 可以，edit 模式 | App → agent-link → zcode-cli 读取数据并修改指定文件，主 Agent 回读确认结果正确、输入未变 |
| Qoder | 本次检测可用 | 小脚本真实请求返回正确短标记，usable=true；后续仍在使用前检测 |
| CBC | 本次检测额度阻断 | 小脚本返回quota_blocked；配置保留，后续使用前重查 |
| DSH | 暂停 | 用户明确暂时不用；历史通过不代表继续启用 |

派发 Qoder/CBC 前先执行：

```bash
python3 scripts/agent_quota_check.py          # 检查两者
python3 scripts/agent_quota_check.py qoder    # 只检查待用 CLI
```

脚本输出 JSON 数组。仅选择 `usable=true` 的目标；`quota_blocked` 表示额度阻断，`rate_limited` 表示请求限流，`unknown`、`timeout` 等不能当成功。它禁用工具、只要求短标记，复用 CLI 原有登录和默认模型；会产生少量模型请求，并非精确余额查询。当前 help/status 未发现可直接使用的余额命令，不新增认证或直连接口。

不缓存永久禁用状态。当前检查失败就换候选，同批不反复检测；下次实际使用前重新检查，额度恢复后自然可用。脚本不输出原始响应、账号字段或凭据，不改登录和默认模型，不启动后台轮询。Qoder/CBC 配置始终保留，DSH 暂停。

ZCode 活动配置已从 `plan` 改为 `edit`。真实测试读取 values.json，修改 summary.txt；主 Agent 独立验证正确总和、输入原文未改、目录仅有原两份文件。该验证不覆盖所有命令执行、会话恢复或后台 queue。

`list_agents.available=true` 只表示命令可执行，上游不检查额度、登录或模型响应。其他自动发现的内置 profile 不在本轮选定范围，不因出现在列表就自动选用。主 Agent 按上述范围派发，再独立验收非空正文和任务结果；遇到额度错误临时跳过该 CLI，当前任务由主 Agent 继续或改派已允许候选，不搭建新的额度服务。

## 如何调用

在 Codex 中明确指定工具、CLI、任务和工作目录：

> 调用 agent-link 的 spawn_agent，agent=agy，cwd=这个项目的绝对路径。让它检查指定文件并返回结果，不再派生其他 Agent。

相应的工具参数：

```json
{
  "agent": "agy",
  "task": "Read the requested file and report the findings. Do not modify files.",
  "cwd": "/absolute/path/to/project",
  "timeoutMs": 120000,
  "retry": false
}
```

`agy`、`zcode` 可按任务选用；`qoder`、`cbc` 先运行上述脚本检测。`cbc` 是 CodeBuddy Code；`zcode` 配置实际执行 `zcode-cli`，不是同名桌面程序。可执行文件存在不代表额度和模型调用可用，当前限制见下表。

当前参数组合如下，提示词由 agent-link 放在末尾：

| agent | command | args | promptFlag | promptMode |
| --- | --- | --- | --- | --- |
| agy | 本机 agy 绝对路径 | --output-format text | --print | arg |
| zcode | 本机 zcode-cli 绝对路径 | --mode edit --no-color | --prompt | arg |
| qoder | 本机 qoder 绝对路径 | --print --output-format text | null | arg |
| cbc | 本机 cbc 绝对路径 | --print --output-format text | null | arg |

各项 outputFormat 为 text。ZCode 当前配置为 edit 模式，指定文件修改已独立验收。ZCode 未配置 modelFlag 或 thinkingFlag。停用 CLI 的历史参数不作为当前派发入口。

上游还提供 `spawn_agents`、`reply`、`kill_agent`、`list_agents`、`get_status`。`reply` 会重新启动 CLI，并传入记录的对话；它不是 CLI 原生会话恢复。服务重启后内存中的对话记录不保留。

## 历史验收

2026-10-25 后续，用户明确要求实测四个 CLI。测试提示不包含答案或随机标记；各 CLI 从独立目录读取 request.json，只对 state=done 的两项求和。主 Agent 独立核对 marker、total=46、count=2 与 MCP 返回。

| CLI | 当前结果 | 说明 |
| --- | --- | --- |
| AGY | 通过 | 修正 --print 参数位置后，App → agent-link → AGY → 当前调用通过 |
| CodeBuddy / CBC | 未通过：额度耗尽 | 原生 stderr 返回 429 额度已用尽；stdout 为空且进程退出 0，agent-link 误报空 done |
| ZCode CLI 0.16.5 | 通过 | 使用 zcode-cli 原生 --prompt，当前配置为只读 plan 模式 |
| DSH 0.2.1-rc.2 | 通过 | 原生 headless 读取文件、返回正确正文并正常结束 |
| Qoder | 此前已通过 | 本日先前已完成真实文档审查，本轮未重复调用 |

CBC 的一次 JSON 输出诊断确认同一额度错误，之后停止请求；未购买额度、换账号或切换模型。上游 agent-link 0.5.3 对 exit 0 只解析 stdout，本轮未改上游。调用者必须核对有意义的结果和实际产物，空 done 不算成功。CBC 保留配置；后续按当前派发范围的额度恢复规则处理，不永久停用。

本轮只修改本机 agent-link 配置和文档，没有新增 CLI 包、wrapper、登录或服务。原生后台 queue、写入、取消与会话恢复不属于这次测试。下文保留早期证据。

2026-10-24，使用 MCP SDK 连接已安装的上游 stdio 服务：

- 握手成功，枚举到六个工具。
- `list_agents` 确认 `agy`、`qoder`、`cbc` 的绝对路径可执行。
- 一次 `spawn_agent(agent=qoder)` 读取本地文件，返回文件中的随机标记和正确和数 96；独立回读结果通过。
- AGY、CodeBuddy 只完成配置与可执行性检查，尚未实测任务。
- Codex 配置读回为 enabled；当日 App 对话的新 MCP 工具加载与实际选择尚未确认。

2026-10-25，原 Codex App 对话实际发现六个 agent-link 工具，并直接调用 `spawn_agent(agent=qoder)` 完成本轮只读文档审查，返回 `status=done` 和能力表、入口冲突及范围建议。主 Agent 对照原文件独立核验主要发现，并据 CapMesh 更新的决定纠正其中过时的 MACPIE 状态。App → agent-link → Qoder → 当前调用的同步路径已验收；不是新增后台 callback，也不代表原生 Codex 子 Agent 生命周期或 AGY/CBC 全部通过。

## 后台接续边界

上游同步工具会等待 CLI 返回结果，没有内置原会话 `codex queue` 回调。若以后增加独立后台派发，完成事件必须按现有约定经 native queue 回原线程。

2026-10-24 检查时旧控制 socket 返回 ENOENT，未设置共享控制通道。2026-10-25 未重查或修改该通道，也未启动替代 daemon、重开 App、发送 queue 消息或新增 callback。agent-link 独立后台接续尚未接入／验收，不能用同步测试代替；既有 queue 历史验收仍按原路径保留。

## 继续与移除

- App 直接调用已在 2026-10-25 的真实审查任务验收；后续按实际任务使用，不反复做同一冒烟测试。
- 若未加载，先检查 App 的 MCP 连接状态；不因包已安装就判断触发已修复。
- 移除 Codex 注册：`codex mcp remove agent-link`。
- 移除 npm 包：`npm uninstall -g agent-link-mcp`。
- 独立配置文件可按需保留或人工编辑。

运行回执保存在本机私有状态目录，不提交到仓库。任务进度见[接入计划](../plans/agent-link-subagent-smoke/task_plan.md)。
