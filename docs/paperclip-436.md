# 436：Paperclip CM 入口

本页只描述 436 试点，不代表本机或其余服务器已经迁移。
当前验收、遗留与接续见[进度](../plans/436-paperclip-feishu/progress.md)。
Paperclip 上游核心和 compat.5 插件源码保持不动。

## 使用

在 436 的有效工作目录中运行：

```sh
cm --help
cm status
cm tasks --json
cm issue create --help
cm agent wake --help
```

`cm`、`controlmesh` 指向[薄入口](../scripts/paperclip/cm-paperclip)，最终执行
`/usr/local/bin/paperclip436`。除 `status`、`tasks` 两个便捷别名外，参数原样传给
Paperclip。创建、分配、唤醒等使用原生 `issue`/`agent` 命令，不再登记旧 Python TaskHub。
不支持的旧命令应明确报错；不要回退到旧 CM。入口不新建调度器、任务状态或模型调用。

root 与 agent436 各有自己的 Paperclip CLI context；公司和 API 地址在目标机配置。
切换 OS 用户时也要进入该用户可访问的工作目录：原生 CLI 会搜索 cwd 的祖先 context，
仅设置 HOME 不能排除误用 `/root/.paperclip/context.json`。不要放宽 root 配置权限。

定时任务新增或变更时使用[失败收敛与磁盘有界规范](cron-safety-contract.md)及其任务模板；
这是后续准入/验收要求，不表示436或其他主机已部署这些门禁。

## 运行归属

- system `paperclip-436.service`：以 agent436 运行，数据在 `/var/lib/paperclip-436`，
  API 仅监听 `127.0.0.1:3100`；工作目录 `/var/lib/agent436/workspace`。
- 飞书复用原「436」应用，通过官方 lark CLI 的 `cm436` profile 与 compat.5 插件收发。
  普通进度卡/收件回执关闭，最终文本回到原线程。Telegram 停用，原身份与配置保留。
- [飞书入口适配](../scripts/paperclip/lark-cm436)：在原群聊过滤之后补全 text/post 可见正文，
  保留 raw 数据，不扩大来源范围。436 旧群配置实际上只有占位群 ID，不能据此声称真实群聊已验收。
- [OpenCode 输出适配](../scripts/paperclip/cm-opencode)：保留当前服务器 GLM 5.1 配置；
  JSON run 缺最终文本时，用同一次 session export 校验 session/message/finish 后补齐。
  export 用私有临时文件防止管道截断，不重新调用模型；归属不明、未完成或部分文本均失败。
- [原独立 watchdog 的飞书版本](../scripts/paperclip/cron-watchdog-436.py)：只迁移通知出口，
  从目标机私有 `cron-notification.json` 读取原会话 chat_id。正常日报只写本地，异常才通知。
  发送失败不记成功；自动暂停后若通知失败，没有额外补发队列，此处不扩建新调度器。

公众号 `wechat-daily.timer`、其 service、root 两条 crontab 与旧 19 项 disabled 任务定义保留。
watchdog 仍独立读取历史 registry；停止 CM daemon 不等于删除 cron。不要重新启用那 19 项任务。
通知发送权限与任务执行权限分开：agent436 的文本验收不代表它可维护所有 root 仓库。

## 审批与证据边界

Paperclip 2026.916.1 的插件 `agents.sessions.sendMessage` 只绑定会话 taskKey，
不接受 issueId/taskId 作为运行归属；compat.5 传入这些字段也不会改变该事实。
因此没有 `PAPERCLIP_TASK_ID` 的插件会话只执行用户工作、交回结果，不自行 checkout/PATCH 单据。
主 Codex 独立核验后通过原生 board CLI/API 收口。需要原生单据执行上下文时用 issue 派发路径；
不要伪造环境变量、绕过权限检查或补丁修改上游。

以下不能互相替代：服务健康、消息收件、模型最终文本、原线程真实回读、主 Agent 审批。
错误的空正文试验保留为失败记录；不能把它的 exit 0 计入功能通过。

## 迁移与恢复

这次是按现场路径逐项实施，不提供自动猜主机、身份或配置的通用安装器。
受限 ZCode 会话提供了薄 CLI；根 Codex 执行已有授权内的 SSH 切换并独立验收。
ZCode 通用安装候选未采用，旧的 `plans/436-paperclip-feishu/bootstrap.sh` 也不是当前部署入口。

目标机恢复材料位于 `/root/migration-backups/cm-paperclip-20261001`，仅 root 可读。
包含原服务/配置/cron/入口与各次验收原始回执；凭据、日志、会话数据不入库。
恢复先在原生 plugin config 中关闭新 subscriber，确认无新消费者后再恢复旧服务。
若仅恢复旧飞书，先把恢复副本的 transports 限为 feishu，遵守用户停用 Telegram 的选择。
不得同时启用新旧同一机器人消费者。恢复 CLI 时逐项还原备份的符号链接，不改 uv 包本体。

## 验证

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider \
  --confcutdir=tests/paperclip_adapters tests/paperclip_adapters
```

测试不调用模型/账号；覆盖输出归属、进程清理、富文本、来源过滤、通知回执与正常静默。
飞书投影另用服务器官方 CLI 的 Go jq 对真实原消息做只读验证。
实时收发与部署状态回源到[本次进度](../plans/436-paperclip-feishu/progress.md)。
