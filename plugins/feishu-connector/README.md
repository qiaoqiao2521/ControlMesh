# 飞书持续私聊适配

本目录维护外部飞书插件的最小扩展。Paperclip 保持官方版本。
普通私聊进入原生 Agent Chat；原有群话题继续使用任务路由。
具体开发、写作和部署仍使用独立执行任务。

## 构建

需要 Python 3、`patch`，以及 Paperclip 2026.916.1 的插件 SDK。
构建器锁定 npm 包 SHA256，再应用既有兼容补丁与精确入口变换。
入口缺失、重复或版本漂移时直接失败，不猜测替换。

```bash
python3 plugins/feishu-connector/build.py --output /tmp/cm-feishu-native-build
```

离线构建可追加 `--tarball /absolute/path/package.tgz`。
输出目录必须不存在。构建器不修改运行目录、不安装、不启用。
`CM-BUILD.json` 记录构建输入与产物哈希。

## 接入

先将构建产物放到 Paperclip 安装根目录的 `local-plugins/`。
这样可以复用安装根目录的官方 SDK。
首次通过原生 `plugin install --local` 加载。
已有插件保留登记路径，受控替换该路径的产物，再通过 `plugin upgrade` 重载。
`install` 会拒绝重复插件键，不能用来升级或迁移已有登记路径。
先验证安装目标、当前活跃运行和旧产物哈希。
如当前 worker 带有额外生产修复，变换该 worker，禁止覆盖为基础重建版本。

在运行用户拥有的目录中创建权限为 `0600` 的配对文件：

```json
{
  "apiBase": "http://127.0.0.1:3100",
  "boardUserId": "local-board",
  "localTrusted": true,
  "bindings": [{
    "companyId": "company-example",
    "agentId": "agent-example",
    "connectionId": "bot-example",
    "senderOpenId": "owner-example",
    "chatId": "private-chat-example"
  }]
}
```

该入口仅适用于原生 `local_trusted` 实例。
CLI 会检查实际 Board 用户，拒绝符号链接和不安全的配置权限。
它不创建登录身份，不读取浏览器凭据，不代理任意飞书用户。

在现有公司级插件配置中追加以下字段，保留其他设置：

```json
{
  "nativeConversation": {
    "enabled": true,
    "command": "/absolute/plugin/dist/native-conversation-cli.py",
    "configPath": "/absolute/private/native-conversation.json",
    "bindings": [{
      "companyId": "company-example",
      "agentId": "agent-example",
      "connectionId": "bot-example",
      "senderOpenId": "owner-example",
      "chatId": "private-chat-example"
    }]
  }
}
```

绑定必须对应同公司、同 Agent 的已有明确 `chat` 或 `user` 路由。
`default` 路由不能证明私聊身份。
通过原生实验设置 API 启用 `enableAgentChat`；CLI 不自动启用。
每个公司、Agent、Board 用户只接一个选定私聊，避免合并不同会话。

## 行为与边界

- 新消息通过原生 chat/comment API 进入同一对话。Paperclip 负责持久会话、排队、唤醒与运行。
- 飞书消息 ID 产生稳定 `clientRequestId`。重复事件不产生第二次模型派发。
- 普通私聊回复留在主聊天流。多个源消息共享同一原生回复时，只发送一次。
- 回执核对公司、用户、Agent、原评论、运行和 generation。不能只按时间找最近回复。
- `/new` 使用原生重置逻辑，保留历史，不手动清空提供商会话文件。
- 插件只保存传输回执。既有完成事件和 30 秒 watchdog 做状态回读，无模型轮询、额外常驻进程或定时 Agent。
- 私聊目前支持文字。附件收到明确限制提示，不悄悄进入旧任务链。
- 问题卡和审批卡提示用户到 Paperclip 处理。飞书文字不冒充卡片提交或审批。
- 无法确认的提交只回读，不自动重新提交。发送前保存意图；发送结果不确定时不自动重发。
- 普通执行任务完成后的协作与独立审批沿用已有机制。本扩展不声称提供新的主管自动唤醒。

丢失提交回执后，CLI 查最近 200 条评论和 200 项运行，最多深入核对 20 项本对话运行。
超窗口或成功运行没有持久回复时返回 `unknown`，不猜测结果。
问题卡在 UI 回答后的 continuation 来源关联尚未做真实验收。
等待记录保留，不把它宣称为飞书交互卡完整闭环。
单次 CLI 最多 20 秒；启动桥最多等待 25 秒。
回执异常与发送不确定记录在 `feishu-native-turn` 实体中，需维护者核对。

## 验证

```bash
python3 -m unittest discover -s plugins/feishu-connector/tests -p 'test_*.py'
node --test plugins/feishu-connector/tests/native-conversation.test.mjs
node plugins/feishu-connector/tests/worker-rpc.test.mjs /absolute/build/output
```

单元与 RPC 验证不代表真实飞书交付。
真实 Paperclip API、生产插件健康和用户新消息验收分别留证据。
当前任务进度见 [SpecMesh 交接](../../plans/feishu-native-conversation-20261006/progress.md)。
