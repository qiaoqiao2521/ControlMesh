# 436 真实飞书持续私聊验收

2026-10-07，Asia/Shanghai。官方 Paperclip 2026.916.1，外部插件 compat.6。
按用户明确要求，用本机已有飞书 CLI 的 user 身份发送合成验收消息。
普通 API 回读确认原 436 机器人实际发送，不以模型报告代替送达。

## 两轮结果

| 请求 | 实际回复 | Run |
| --- | --- | --- |
| 指定验收代号，要求只回复“记住了” | 记住了 | `2a1223d9-0583-4dda-a289-ba926b92ffa4` |
| 不提供代号，询问刚才代号 | 松果灯 | `3d8f00da-fcf6-4511-8aa7-26dcbe07149b` |

两条源消息分别在 00:17:44、00:22:29 发送，均为新的私聊主聊天消息。
两次复用 Conversation Issue `7507f19d-8a04-41f5-ac68-9c1e6d549e59`。
第一轮 sessionIdAfter 与第二轮 sessionIdBefore/After 均为 `ses_eedfde198ffer3GsNNoDvR0Ym7`。
两个 Run 均 succeeded；核心 presentationDecision 指向下表实际回复评论。

| 角色 | 第一条 | 第二条 |
| --- | --- | --- |
| 飞书源消息 | `om_x100b6365bc4d2ca0b1f49bc5686f04e` | `om_x100b63664a9a30a0b4894625a06c833` |
| 原生源评论 | `30ecebef-6922-46de-8a4b-ceac170a183d` | `341af041-0dd5-471b-8c2d-2e37956e62f1` |
| 原生回复评论 | `abf9746e-36b8-434e-b90e-3e4d5ad27c1a` | `f65d84d0-f87f-4310-8331-155f39b86256` |
| 飞书实际回复 | `om_x100b6365bb0c10a4c39746396087bbd` | `om_x100b636649b678a0c02075e15bafccb` |

飞书普通 GET 独立确认：发送者为原 436 app，正文准确，每个 parent_id 对应源消息，thread_id 为 null。每个源消息只有一条对应回复。
CLI status 的公司、Agent、对话、源评论、Run 与回复评论逐条一致。

## 受控部署

- 服务仍是 `paperclip-436.service`，以 agent436 UID 1000 运行；主进程 PID 未变。
- 插件 ID `396c0386-4b21-4788-b6ec-c5b4de901eb2`、登记路径和原机器人身份保留。
- 通过官方 upgrade 重载 compat.6，不卸载、不清理持久数据、不重启 Paperclip 核心。
- 以现场 worker SHA256 `4d2119a6369921399bdb7685f361f27deddea1d34de3e22524bfb4a02f3b9ed0` 为基线，只增加原生入口，保留原七项生产守卫和 CLI 传输适配。
- 现用 worker SHA256 `07fabc6e854957cc1e9a42e87714d352c51289d44912aea3ba724263f1e9ab18`。
- 原连接和配置保持；只追加明确的 owner 私聊路由与 nativeConversation。Board 身份及 local_trusted 现场核对通过。
- 只启用原生 enableAgentChat 功能字段，保留其他实验设置。
- 长期职责修正一次性 Article98 限制；完整旧角色保存在实验记录，只有显式实验任务才使用。
- 当前模型为已配置国内 Coding Plan 的 `zhipu-coding-plan/GLM-5.3-Flash`，见[独立模型验收](436-provider-verification.md)。

## 恢复与限制

旧插件、旧公司配置、角色、实验设置和配对文件保存在服务器私有目录 `/var/lib/paperclip-436/native-feishu-20261007/`，目录 0700、配置 0600。恢复前核对当前 worker 哈希和在途运行，只对原插件做受控升级，不恢复旧 Python 服务，不删除任务或回执。恢复未实际执行。

既有 `/usr/local/bin/lark-cm436`、传输适配器、私有 OperationStore、原 cron、浏览器与账号保留。未修改 Paperclip 核心，未操作其他服务器。

当前结论只覆盖原生文本持续私聊、实际普通用户模型运行与主聊天一次送达。群任务既有修复保留，新的卡片交互、附件模型读取、UI continuation 与主管唤醒没有据此验收。
