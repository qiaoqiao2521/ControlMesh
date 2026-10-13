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
已有插件保留登记路径，按下文暂停、完整发布、启用的门禁替换产物。
`install` 会拒绝重复插件键，不能用来升级或迁移已有登记路径。
先验证安装目标、当前活跃运行和旧产物哈希。
如当前 worker 带有额外生产修复，变换该 worker，禁止覆盖为基础重建版本。

compat.9 增加启动恢复和纯运行检查，保留 compat.8 的消息接纳与回执规则。
在部署目录 `dist/cm-company-binding.json` 中显式保存以下非秘密身份。
文件必须为普通文件，不可为符号链接，不允许组或其他用户写入。
缺少文件时 setup 不猜测公司；后续官方明确配置回放仍可绑定。
存在但格式、归属或官方公司授权错误时，初始化失败。

```json
{"schema":"cm.feishu.deployment.v1","pluginKey":"paperclipai.feishu-connector","companyId":"explicit-company-id"}
```

worker 在 setup 中通过官方 `config.get(companyId)` 恢复当前持久配置。
宿主必须已授权该公司；侧车文件不能绕过租户边界。
相同配置回放复用监听和定时器。其他公司的空历史行不改变身份，非空配置拒绝。
setup 不执行完整旧数据库同步或等待原生 pending 投递，避免超过宿主15秒初始化限制。
既有完成事件和30秒 watchdog 接续状态回读，不新增模型调用。

发布前核对原身份、完整配置、所有公司的在途运行、旧产物哈希和 capabilities。
只有能力列表完全不变的发布才可使用原生 disable → 完整替换 → enable。
新增能力仍走官方 upgrade 审批，不用 enable 绕过权限升级。
先暂停插件并确认 worker 已停，再完整替换代码及本机公司侧车，保留生产守卫。
最后一次写入后确认仍 disabled、无 worker、产物哈希正确，再启用并 GET 回读实际版本。
Paperclip 2026.916.1 的 HTTP 路由与文件监听器使用不同 lifecycle 对象，
不能仅凭 disable 返回就认定文件监听已撤销。还须等待文件稳定及500毫秒 debounce，
检查可用的拒绝日志或静默现场，并在启用后复核监听、watchdog 与真实回复。
disabled 状态不能直接 upgrade；不得同时写文件和调用 upgrade。

将仓库 `scripts/paperclip/cm-feishu-runtime` 安装到现有 CLI 目录。
它仅有两个动作，不读取浏览器凭据，不创建 Agent、守护或 cron。

```bash
cm-feishu-runtime check --plugin-id explicit-plugin-id --company-id explicit-company-id
cm-feishu-runtime sync --plugin-id explicit-plugin-id --company-id explicit-company-id
```

`check` 查询原生 API 和纯内存 `runtime-health`；不启动或修复监听。
它核对公司、当前配置指纹、期望与实际监听数，以及 watchdog 时间。
启用的 chat/user 路由还必须有非空 chatId/userId；禁用草稿保留。
watchdog 超过90秒拒绝；尚无首 tick 时仅允许60秒启动窗口。
`sync` 仅写明确公司的非秘密侧车，并在已完整发布 compat.9、插件 ready 且无在途任务时调用官方 upgrade。
它不 POST config，不自动处理 error/disabled，不重试结果不明的升级。
文件、配置或公司冲突直接拒绝；未配置返回3，未知升级结果返回4。
两个动作成功也只代表运行基线，输出始终含 `deliveryVerified:false`。

最后发出一个明确的新验收消息，从原 App、原聊天回读唯一回复。
`status` 数据桥会 reconcile 订阅器，属于恢复动作；不要拿它冒充纯检查。
历史原样重应用 configJson 的恢复见10月13日证据，不能替代当前启动恢复与现场验收。

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
路由 `replyMode` 使用 `message`；该版本只接受 `none`、`message`、`thread`。
`senderOpenId` 必须来自此机器人 App 的身份绑定或官方成员回读。
本机 user CLI 的 OpenID 属于另一个 App，不能直接复制到机器人配对。
通过原生实验设置 API 启用 `enableAgentChat`；CLI 不自动启用。
每个公司、Agent、Board 用户只接一个选定私聊，避免合并不同会话。

凭据被上游明确拒绝时，在保留现有公司配置的前提下设
`enableEventSubscriber=false`，回读无活跃订阅器，避免持续失败重连。
`eventSubscriberEnabled` 是状态结果字段，不能用作配置开关。
修复原 App 凭据后再启用并验收新消息，不以插件 `ready` 判断恢复。

## 行为与边界

- 新消息通过原生 chat/comment API 进入同一对话。Paperclip 负责持久会话、排队、唤醒与运行。
- 飞书消息 ID 产生稳定 `clientRequestId`。重复事件不产生第二次模型派发。
- compat.8 先查原生回执，再只读核对旧 session 和 dedup。旧入口已接纳的消息仍由旧入口负责；未知送达不自动转为新任务。
- 升级前误入原生 pending 的旧消息，核对原绑定后记为 `legacy_retained`，保留实体与历史，不新增状态调用或回复。已确认的原生 ACK 继续原恢复。
- 旧 Agent 已迁移时，通过官方只读 Agent/Issue API 核对原公司归属；缺失、跨公司或无权限时拒绝，不改写旧 ownership。
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
node --test plugins/feishu-connector/tests/native-runtime.test.mjs
python3 -m unittest discover -s tests/paperclip -p 'test_feishu_runtime_gate.py'
node plugins/feishu-connector/tests/worker-rpc.test.mjs /absolute/build/output
```

单元与 RPC 验证不代表真实飞书交付。
真实 Paperclip API、生产插件健康和用户新消息验收分别留证据。
当前任务进度见 [SpecMesh 交接](../../plans/feishu-native-conversation-20261006/progress.md)。
六机接入与单机诊断见 [2026-10-12 证据](../../plans/feishu-native-conversation-20261006/evidence/fleet-live-20261012.md)。
启动恢复与逐机门禁见 [2026-10-14 证据](../../plans/feishu-native-conversation-20261006/evidence/fleet-runtime-guard-20261014.md)。
