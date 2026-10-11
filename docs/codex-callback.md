# Codex 原会话完成回调

CM 是工作流概念与薄适配层，Paperclip 拥有派发和任务生命周期。本机回调使用固定版本的 [codex_callback](../vendor/codex_callback/UPSTREAM.md)，将外部完成通知送入原 Codex 会话的 native queue。

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

## 竞态与恢复

桌面可能在 worker 调用 queue/start 前先消费消息。此时按同一 event/client ID 查询原线程历史回执；无法确认就保留不确定状态，不新增队列项。补丁范围与上游差异见 [UPSTREAM.md](../vendor/codex_callback/UPSTREAM.md)。

通知创建中断时，重复调用只核对原来的私有 callback 目录。发现 worker 进展或接续回执后可恢复关联；只有 pending 文件、目录不存在、记录不完整或存在冲突时继续保留待对账。不要删除保留记录后重试，以免重复投递。

## 验证与接续

隔离测试不运行真实 worker，也不投递 native queue。当前进度与验证命令见 [progress.md](../plans/codex-callback-bridge/progress.md)。在本机任务的完成钩子中调用 notify，再由原会话读取交接文件。跨主机传输不属于本次范围。

## 原生完成事件试用

本机 Paperclip 2026.916.1 提供 `/api/companies/<company>/events/ws`。其 `heartbeat.run.status` 事件包含 run、issue、agent 和终态。薄入口 [cm-codex-native-watch.mjs](../scripts/paperclip/cm-codex-native-watch.mjs) 订阅这一现有接口，不修改 Paperclip 或飞书插件。

当前只支持明确的 `127.0.0.1:3100`、`local_trusted` 实例和 Node 22+ 内置 WebSocket。它绑定一个 company/issue/agent，先生成订阅就绪记录，再由原生入口派发。终态事件触发后，重新查询 run 和关联 issue，核验 worker 回执与文件哈希，然后调用既有 notify。它不轮询、不执行模型、不创建任务或恢复失败运行。

每次订阅最多 20 分钟，只接一个 run，结束后退出。连接中断、不同 run、缺失产物或未知通知结果均保存错误并停止，不自动重连或重发。它没有补历史事件的保证；操作者应从保留记录核验，不能假设长期或断线恢复已验收。

其他明确绑定任务可以在本机 spec.json 设置 `followup`，长度为 1–8000 字符。它保存在交接文件中，说明该任务的独立验收与接续入口；未设置时保留原研究试用说明。该字段不改写绑定线程、company/issue/agent、notify 去重或完成证据要求，也不让回执自动成为业务接受。

QIA-100 试用 [cm-local-model-research](../scripts/paperclip/cm-local-model-research)，复用 Night Lab 的研究调用、来源回执和 JSON 校验。一轮 GLM 研究产生待审草稿，临时 Paperclip 凭据不传给模型。运行保留记录拒绝同任务自动重跑；未安装或下载本地模型。其草稿不冒充四阶段互审已通过知识卡。

本次真实试用已通过原生派发、完成事件自动 notify、忙时入队、同原会话唯一持久 turn 与文件独立读回。草稿独立审查需要修订，issue 保持 in_review；一次性 Agent 已暂停。验收与审查证据私有保存。该结果只覆盖本次明确绑定任务，不扩展为后续任务自动绑定、断线恢复或模型部署通过。

独立事件边界测试：

```sh
node --test tests/paperclip_adapters/test_codex_native_watch.mjs
```
