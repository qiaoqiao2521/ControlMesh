# 本机真实飞书持续私聊验收

2026-10-07，Paperclip 2026.916.1，外部插件 compat.6。
按用户明确要求，用已有飞书 CLI 的 user 身份发送测试。
CLI auth status 的 user openId 与私聊绑定一致；没有扩权、新建机器人或复制认证。

## 结果

两条消息直接发到私聊主聊天，各自没有沿用旧消息 root。

| 请求 | 实际回复 | 原生运行 |
| --- | --- | --- |
| 记住验收代号，要求只回复“记住了” | 记住了 | `99389991-39c6-4780-93e6-1473546d47bd` |
| 不提供代号，询问刚才代号 | 竹叶舟 | `585b7100-f961-4639-9695-c17c5e70dd81` |

两次复用 Conversation Issue `QIA-75` / `015461cf-1e5b-49da-9a6c-8d67ba1a921c`。
第一次 sessionIdAfter 与第二次 sessionIdBefore/After 均为 `01a111f5-5734-7fb3-8f9d-9a7e22823e12`。
两次 Run 均 `succeeded`，核心 presentationDecision 明确选择实际回复评论。
CLI status 的源评论、Run 和回复评论逐条绑定一致。

| 角色 | 第一条 | 第二条 |
| --- | --- | --- |
| 飞书源消息 | `om_x100b6365f1a408a0b2c4a7e6ad431e7` | `om_x100b6365862fa0a8b26d07c457d3c28` |
| 原生源评论 | `41943e9b-e508-4a9e-bc7c-b4b84ff1917b` | `d89fa8fa-b89f-4107-83ba-4a203bb576fb` |
| 原生回复评论 | `5cd98775-a297-4ab7-a5fb-26c2988d8595` | `c8c35d44-2e61-42ed-afea-98575e7c93a3` |
| 飞书实际回复 | `om_x100b63658cb2c0a0b10cd3052e6d691` | `om_x100b636585dad4a4b256d2574076ade` |

通过飞书普通 GET 独立回读，回复正文准确，发送者是原本机机器人。
每个 parent_id 匹配其源消息，thread_id 为 null，回复出现在主聊天流。
每条源消息只有一条对应回复。

## 部署与保留

- 插件 ID 与原登记路径保留。原生 upgrade 后版本 compat.6、status ready。
- SDK status 显示一个 listener，profile 可用，monitor 为 ok。
- 原连接、路由与配置字段逐项保持；只追加显式 nativeConversation。
- 长期职责新增原生对话与独立执行任务边界，修正默认提交推送准则。
- 旧配置、角色及插件代码在运行用户私有目录保留，权限 0700/0600。
- 未重启 Paperclip 核心，未改变公众号任务或机器人身份。

存在一条升级前遗留的超时回复 retry，原结果为发送状态不确定。
保留记录，未替用户再次发送。新原生分支不进入旧自动重试队列。

此验收覆盖普通私聊与模型会话连续性。卡片提交、UI continuation 和执行任务主管自动唤醒不在此结论内。
