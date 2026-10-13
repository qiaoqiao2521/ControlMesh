# 六机飞书启动恢复与运行门禁

2026-10-14。范围为本机及 BF、436、Green、Moon、Cy、Qia。
meiren、国内 legacy 不接入。使用既有 SSH；Green 经 Tailscale，其余五机公网直连。
root 只做维护，Paperclip 与插件继续由 UID1000 运行。未改网络或增加 Agent cron。

## 已确认的问题

BF 和昨日436一样：静态健康、注册 ready、持久配置正确，实际没有公司上下文与监听。
BF 原配置原样重应用后恢复，configJson 指纹仍为
`0ec8ebd3cbdefdd43bfc7292003d930a652ba8e9845f7b60b0475e6693f862b5`。
这次独立核对 SDK：worker-manager 的单独重启只 initialize，不经过 loader 的配置回放。
不能把“宿主有回放逻辑”解释为每一条重启路径都会回放。
昨日436当次触发的确切原因仍未证明；这个已确认的恢复缺口单独修复。

Cy 已有独立 App 与监听，但启用的 chat 路由没有 chatId。
原机器人回读验收源，结合本机 user CLI 的 p2p 清单核对真实私聊。
首次只补 `routes[owner-p2p-cyrise].chatId`，其他配置和 native 模式保持。
首次路由修补的配置指纹由 `51f248c039dde28bb8b273318aa761861e093dc3f55f9e93f297a17e3a2ba086`
变为 `053a41a230364bbf66774ffc71b4fe0a5ace7d41580ed2f1ca07adc5745683a6`。
此次更新没有产生模型运行；旧未匹配的测试源保留，不补投。
新源随后被旧任务路由接纳，CMC-114／`df1be680-79df-4a03-bf5b-aebe22dde6df`
的运行 `167b8af0-59fc-4266-916c-113f88c59a2a` succeeded，但没有实际回复。
运行成功不代表旧传输完成，也不能再次用native接纳该源。
按原计划补齐nativeConversation：原App官方回读sender范围，实际local-board身份，
私有五字段配对0600/UID1000，实例enableAgentChat从false启用。
配对先通过纯status返回not_found验证，无模型运行；原配置、模型、群路由与旧Issue保留。
新的native验收源独立发送，不补投此前两个源。
已回读原「云栈」App在主聊天唯一回复“Cy持续私聊验收通过”。

## 最小实现

- compat.9 在 setup 读取模块旁非秘密公司侧车，再通过官方授权 config.get 恢复配置。
- 相同配置回放复用监听；其他公司空历史行不捕获身份，非空配置拒绝。
- 保留原 native8 接纳、去重、回执、生产回复守卫、Moon shim 与 AGY collector。
- setup 不做完整旧数据库同步，不等待 pending 投递；原完成事件与30秒 watchdog 接续。
- runtime-health 纯读内存。静态 ready 之外，核对已应用配置、监听数与恢复循环。
- 一个标准库 CLI，仅 check/sync；未配置、半路由、身份冲突、在途工作和未知升级结果均拒绝。
- sync 不 POST config，不调用模型，不发送消息，不新建守护。

CLI 成功始终输出 `deliveryVerified:false`。调用方仍须验证原 App、原聊天中的实际回复。
27项 capabilities 完全不变，官方 Paperclip 源码未修改。

## 发布中的现场纠正

BF 首次完整发布后立即 upgrade，与官方 dev-watcher 同时重启，initialize 期间被停止。
真实错误为 worker exited(code=0)，不是模型调用成功。
BF、Green 的 SDK/loader/worker-manager 与本机版本一致；不是旧 SDK 的解释。

Green 随后验证：HTTP 路由和 app dev-watcher 使用两个 lifecycle 实例。
所以 HTTP disable 的事件没有传到该 watcher，不能仅看单模块 unwatch 函数认定已撤监听。
源码的文件稳定等待为200毫秒、轮询100毫秒、debounce 500毫秒。
最终按空闲门禁暂停、确认无 worker、完整发布、保持 disabled 等待回调结束，再启用。
回读注册版本、源哈希、配置、主进程与运行状态。可用日志里的 disabled 拒绝是附加证据。
Moon 没有取得该拒绝日志，不伪造；它停在 disabled 后确认无 worker及完整产物，再启用并验收。
固定等待本身不是完整排空证明，启用后的稳定监听、watchdog 与实际回复仍必须回读。

发布能力列表须与登记值完全相同。enable 的 manifest 刷新不替代新增能力的官方升级审批。
disabled 不能直接 upgrade。不能同时改文件和发 upgrade。

## 本轮状态

| 设备 | 版本与运行 | 实际回复与边界 |
| --- | --- | --- |
| 本机 | compat.9、唯一监听、watchdog推进；两公司中显式绑定实际公司 | worker-only重启后回复“本机冷启动验收通过”，原 App、主聊天一次 |
| BF | compat.9；原配置、主服务、原机器人保留 | 回复“BF监听加固验收通过”，主聊天一次 |
| Green | compat.9；原配置、主服务和旧 pending保留 | 回复“Green监听加固验收通过”，主聊天一次 |
| Moon | compat.9；原 App、shim、collector和配置保留 | 回复“Moon监听加固验收通过”，主聊天一次；纠正10月12日过期状态 |
| Cy | compat.9；独立App；补齐chat路由与已计划的native持续私聊 | 回复“Cy持续私聊验收通过”，主聊天一次；旧任务接纳与运行保留，不重派 |
| Qia | compat.9，但公司配置为 null；不创建侧车或 CM 监听 | 既有 owner-event → Codex App 桥保留；独立 CM 尚未配置 |
| 436 | compat.9；等待在途运行自然结束后通过空闲预检并发布 | 配置、主进程和生产守卫保留；回复“436启动加固验收通过”，主聊天一次 |

本机现场只结束已核对为空闲的原插件 worker。
PID由1114509变为1115170，manager401510保持，未发 upgrade 或 config POST。
新 worker 自行恢复唯一监听，公司配置不变、没有新增运行。
这验证 SDK 自动重启路径；实际新消息另由 Feishu API回读。

| 设备 | 新测试来源 | 原 App 回复 |
| --- | --- | --- |
| 本机 | om_x100b63d37e7924a0cf06109e6f2f7a9 | om_x100b63d37c4ac0a4cee5d0dbb2ac919 |
| BF | om_x100b63d37e0f1ca0cff35d77b9191b6 | om_x100b63d37dbaf8a0de860c74ebde1b7 |
| Green | om_x100b63d37e1c3ca4ce782b785064c78 | om_x100b63d37588e8a4b0747a9b1f1c365 |
| Moon | om_x100b63d30107f8a4b096f25d0fd9100 | om_x100b63d31d271ca4dffffcffeb64d62 |
| Cy | om_x100b63d3979fe0a0cd26ce334c17998 | om_x100b63d392698ca0cfee0b088f06afd |
| 436 | om_x100b63d3bab318a8b08742a9d881d23 | om_x100b63d3b91b58a4dfcd922d3fb3fc2 |

上述回复内容均为合成口令，thread_id均为null，每条一次。
Cy 第一条 `om_x100b63d301110ca8ce791bdb7ec49a5` 未匹配路由，未补投。
补齐后新测试来源 `om_x100b63d3c7a68ca0cf83b5a0b001aea` 单独留证。
native新测试来源为 `om_x100b63d3979fe0a0cd26ce334c17998`。

## 验证与接续

53项插件 Python、27项 CLI、51项 Node 单元验证通过。
40项真实 SDK/worker-manager 回归通过；Green、Moon生产候选各28项 native-only RPC通过。
测试涵盖单独重启、foreign空配置、SDK授权、纯health零I/O、配置指纹、并发配置与在途任务。
真实部署不能用这些离线结果替代。CLI最终 SHA256为
`41c56f9b72b139b7d227bbfcde27bcdff6d7bc5786cc3591c5400085bcf485aa`。
native-runtime SHA256为 `98df3b70aa70d523e80055523d5b51cb28baab0a91decf281b8b8d631428e9ff`。

436最终纯check确认唯一监听、配置指纹不变、watchdog从空首tick持续推进。
根Codex负责Qia独立身份及Green/Cy历史测试回执核对。
436原任务保留原评论与队列，不再投递旧23:25源；本批仅验收新合成源的收发，不代替旧业务质量审批。
本机私有 code rollback、源代码候选和白名单回执在原任务 work/fleet-feishu-guard-20261014/；不提交配置、凭据或运行日志。
