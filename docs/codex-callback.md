# Codex 原会话完成回调

## 当前范围（2026-10-20）

CM 当前方向是单 Harness 内的多 Agent 协作，并加入 MACPIE 模型统筹职责；具体组件身份与接入待确认。hcom 跨 Harness 接入移出后续计划。本文仅维护已有 Codex App native queue 路径，不构成继续研究跨 Harness 的任务。详见[最新决策](DECISIONS.md#2026-10-20--单-harness-协作与模型统筹)。

下文 `cm-codex-callback` 和 `cm-codex-task` 是已实现的 Paperclip 专用路径，仍要求其原生身份与回执契约，不能直接拿任意 CLI 的退出码冒充 Paperclip run。社区 `codex_callback` 的通知基础保留；不扩展为通用 CLI 互通层，本次没有新增或验证该路径。

在本文已实现的 Paperclip 专用桥中，Paperclip 拥有派发和任务生命周期。本机回调使用固定版本的 [codex_callback](../vendor/codex_callback/UPSTREAM.md)，将外部完成通知送入原 Codex 会话的 native queue。

独立入口是 [cm-codex-callback](../scripts/paperclip/cm-codex-callback)。它提供绑定、一次通知和回执查询，不接管任务执行。本机原有的 `cm` 入口保持现状；436 的 `cm-paperclip` 是目标机模板，不能当作本机 Paperclip 安装。

## 运行条件

- Codex App 和回调客户端必须连到同一个 daemon，原线程必须已 loaded。
- 在发起任务的 Codex 会话中保存 binding。默认线程 ID 取自 `CODEX_THREAD_ID`。
- 完成钩子先核对原生 company、issue、run 与执行结果，再调用本机通知入口。
- 交接文件必须先落到 binding 的本机工作目录内。远端文件地址不能直接作为本机路径。

交接文件最多 2 MiB。大型产物放在工作目录中，由交接文件记录位置与证据。

用户选定只接本机。本机已做同服务原线程的只读预检，不操作 436 或其他远端。App 下次普通启动的持久连接仍需另行验收。首次 idle/busy 两事件验收记录原貌保留。

后续用户授权以真实已结束任务试用。Night Lab 的 cm.json 指向现有本机 Paperclip 127.0.0.1:3100，不能因没有 CLI 推断实例不存在。已有结果补发与持续完成钩子分别验收；不重跑已有任务来测试通知。

## 绑定原会话

条件：Paperclip 已返回尚未唤醒的原任务编号，当前 shell 属于发起任务的 Codex 会话。

```sh
cm-codex-callback bind \
  --company-id "$CM_COMPANY_ID" \
  --issue-id "$CM_ISSUE_ID" \
  --cwd "$PWD"
```

绑定会检查原线程是否 loaded、线程 ID 和 cwd 是否匹配，以及是否允许输入。绑定成功后，使用当前任务原有的派发与唤醒入口执行任务。此命令不创建任务，也不改变默认 CM 运行底座。

默认 socket 为 `~/.codex/app-server-control/app-server-control.sock`。需要其他明确服务时，在 bind 加 `--socket-path`；完成事件不能改写目的线程或服务地址。

## 接收完成事件

条件：完成钩子已核对原生归属，并把交接文件完整保存到本机 binding 的工作目录。

```sh
cm-codex-callback notify \
  --company-id "$CM_COMPANY_ID" \
  --issue-id "$CM_ISSUE_ID" \
  --run-id "$CM_RUN_ID" \
  --outcome completed \
  --handoff "$PWD/output/handoff.json"
```

映射原生终态时，使用 `succeeded → completed`、`failed → failed`、`timed_out → timed_out`、`cancelled → cancelled`。不能仅因 issue 为 `done` 就报告执行成功；已有 CM worker 的失败交接也可能标为 done。

命令记录交接文件 SHA256，再调用社区 `notify()`。相同 run 和相同完成内容不会再次创建 callback；相同 run 的冲突内容会报错。创建结果未知时保留 `needs_reconciliation`，不会自动重发。

状态和锁位于私有 `~/.local/state/cm-codex-callback`。测试或明确隔离目录时，为三个命令一致传入 `--state-dir`；不要将运行目录提交进 Git。

## 查询回执

```sh
cm-codex-callback status \
  --company-id "$CM_COMPANY_ID" \
  --issue-id "$CM_ISSUE_ID" \
  --run-id "$CM_RUN_ID"
```

`queued` 表示入队。`started` 和 `turn_id` 表示原会话开始接续。它们都不能证明业务结果已验收，输出中的 `followup_complete` 与 `business_accepted` 保持 false。

原 Codex 会话收到通知后，读取交接文件，核对原线程、任务编号和 SHA256，再独立检查结果。接受、返工或报告失败由原会话决定；适配器不自动创建下一项任务。

## 准则继承与任务范围

本项目准则见 [AGENTS.md](../AGENTS.md#复用与流程成本)。协调 Agent 在派发前读取实际目标项目的 AGENTS、PROJECT 和相关计划，将本次采用的准则、交付物和停止条件放进已有原生 issue 或 worker 任务上下文。`cm-codex-task` 只启动已经配置的任务，不生成 worker prompt，也不证明外部 worker 已读取文档。

新 callback 的接续文字提醒原 Agent 重读绑定项目当前入口，遵循最新用户范围，先复用已有工具或上游实现，并按任务选择验证。有效的部分结果或人工交接可以满足需求；不为形式上的完整闭环增加工作。仍须核对身份、原 run 和产物，不能把这种提醒当成业务验收。

新事件在私有 event.json 保存 `followup_version=2`，状态输出也返回该版本。旧事件没有此字段时按版本 1 精确比对原文，恢复不会升级提示或改写原 handoff。未知版本拒绝对账。以后改提示时增加版本，保留已有版本的文字；不要重发旧 callback 来更新规则。

隔离测试验证消息内容、旧回执兼容和去重。Agent 是否实际采用准则，仍要从原会话动作与结果核查；下一个授权任务可沿已有日志检查，无需额外任务或日志库。

## 竞态与恢复

桌面可能在 worker 调用 queue/start 前先消费消息。此时按同一 event/client ID 查询原线程历史回执；无法确认就保留不确定状态，不新增队列项。补丁范围与上游差异见 [UPSTREAM.md](../vendor/codex_callback/UPSTREAM.md)。

通知创建中断时，重复调用只核对原来的私有 callback 目录。发现 worker 进展或接续回执后可恢复关联；只有 pending 文件、目录不存在、记录不完整或存在冲突时继续保留待对账。不要删除保留记录后重试，以免重复投递。

## 验证与接续

隔离测试不运行真实 worker，也不投递 native queue。当前进度与验证命令见 [progress.md](../plans/codex-callback-bridge/progress.md)。在本机任务的完成钩子中调用 notify，再由原会话读取交接文件。跨主机传输不属于本次范围。

## 原生完成事件试用

本机 Paperclip 2026.916.1 提供 `/api/companies/<company>/events/ws`。其 `heartbeat.run.status` 事件包含 run、issue、agent 和终态。薄入口 [cm-codex-native-watch.mjs](../scripts/paperclip/cm-codex-native-watch.mjs) 订阅这一现有接口，不修改 Paperclip 或飞书插件。

当前只支持明确的 `127.0.0.1:3100`、`local_trusted` 实例和 Node 22+ 内置 WebSocket。它绑定一个 company/issue/agent，先生成订阅就绪记录，再由原生入口派发。终态事件触发后，重新查询 run 和关联 issue，核验 worker 回执与文件哈希，然后调用既有 notify。它不轮询、不执行模型、不创建任务或恢复失败运行。

每次订阅最多 20 分钟，只接一个 run，结束后退出。连接中断、不同 run、缺失产物或未知通知结果均保存错误并停止，不自动重连或重发。它没有补历史事件的保证；操作者应从保留记录核验，不能假设长期或断线恢复已验收。

其他明确绑定任务可以在本机 spec.json 设置 `followup`，长度为 1–8000 字符。它保存在交接文件中，说明该任务的独立验收与接续入口；新 handoff 未设置时使用上述通用项目准则提醒，原研究专用说明仅保留在历史 handoff。该字段不改写绑定线程、company/issue/agent、notify 去重或完成证据要求，也不让回执自动成为业务接受。当前成功 worker 回执仍要求 `draft_for_review` 与至少两份产物；通用提示不扩大此契约的适用范围。

QIA-100 试用 [cm-local-model-research](../scripts/paperclip/cm-local-model-research)，复用 Night Lab 的研究调用、来源回执和 JSON 校验。一轮 GLM 研究产生待审草稿，临时 Paperclip 凭据不传给模型。运行保留记录拒绝同任务自动重跑；未安装或下载本地模型。其草稿不冒充四阶段互审已通过知识卡。

本次真实试用已通过原生派发、完成事件自动 notify、忙时入队、同原会话唯一持久 turn 与文件独立读回。草稿独立审查需要修订，issue 保持 in_review；一次性 Agent 已暂停。验收与审查证据私有保存。该结果只覆盖本次明确绑定任务，不扩展为后续任务自动绑定、断线恢复或模型部署通过。

上述是 2026-10-11 首次审查记录。2026-10-12 已逐项修复并接受研究修订，issue=done 读回；原草稿与回传证据未改写。恢复入口也在原 QIA-100 运行对账通过，已有 callback 回执完全一致。当前边界见 [进度](../plans/codex-callback-bridge/progress.md)。

独立事件边界测试：

```sh
node --test tests/paperclip_adapters/test_codex_native_watch.mjs
```

## 本机任务启动与恢复

2026-10-12 补齐 [cm-codex-task.mjs](../scripts/paperclip/cm-codex-task.mjs)。它组合既有 bind、原生订阅、Paperclip 派发与 notify，不创建任务或替代调度器。仅适用于上述本机实例、已明确绑定的单任务与 worker 回执契约。

条件：任务已创建为 backlog，spec.json 在本机工作目录内；当前 Codex 会话是 spec 指定的原会话。

```sh
cm-codex-task launch /absolute/task/spec.json
```

spec 必须包含 `native_base`、`company_id`、`issue_id`、`agent_id`、`thread_id`、`directory`。directory 必须是 spec 所在真实目录，并处于当前工作目录内。可选 followup 说明业务独立验收。此命令先检查 native 归属和原线程，保存绑定并订阅；只有就绪与任务归属再次确认后才把原任务改为 todo。命令等待本次 watcher 结束，回执不自动接受业务结果。

派发前落盘独占 attempt 并 fsync；响应丢失保留 unknown，继续已有订阅，不自动再次派发。已存在任何 attempt 的启动会被拒绝。普通 App 重启、持久后台服务和跨机恢复仍未验收。

条件：已确认原来的 run ID，运行已终止；订阅中断或缺失终态事件。

```sh
cm-codex-task reconcile /absolute/task/spec.json ORIGINAL_RUN_ID
```

恢复只读取原生 run、issue 及关联记录，复核原 worker 文件和哈希，再调用既有去重通知。它不 PATCH 任务，不执行模型。交接证据标记 `native_terminal_readback`，不冒充收到 WebSocket 事件。已存在交接文件必须身份与哈希一致，原件不改写；未知 queue 结果仍按原适配器保留待对账。

```sh
node --test tests/paperclip_adapters/test_codex_native_watch.mjs tests/paperclip_adapters/test_codex_task.mjs
```
