# 436 飞书收件恢复

2026-10-13，Asia/Shanghai。仅处理 racknerd-436b0c0 原飞书入口。
原 App cli_aa99f084ed38dbd7；公司5dde8cef-0b64-44a3-a6e3-17774326aaea；插件396c0386-4b21-4788-b6ec-c5b4de901eb2。

## 原症状与定位

23:25 原源消息 `om_x100b63d099ccb0accd17a6919a9df35` 已在飞书，尚未进入原生对话或产生 main Agent 运行。
Paperclip 和数据库 health=ok，main Agent idle；不能归为模型故障。
主进程 PID3803608、插件 worker PID1567954 均 UID1000，compat.8 代码哈希与昨日一致。
完整进程树中没有 SDK/飞书订阅子进程；原路由、App、native binding 和 enableEventSubscriber=true 仍正确。

worker 创建于10月12日09:57:50Z，与昨日 compat.8 升级同时，此后没有自动重建。
公司级只读 `catalog` 数据桥返回502，错误指向未建立 company-scoped configuration；证明新 worker 没有应用持久配置。
官方 GET plugin health 只核 registry、manifest、状态，不能证明订阅进程运行。
昨天接受了版本和配置回读，却没有接受升级后的实际收件链；该验收缺口已纠正。

当前安装的宿主 loader 源码包含 best-effort startup configChanged 回放。
回放具体未成功的原因尚未确定，不能声称上游已经没有回放或已经修复其根因。
恢复 flush 抛错可能阻止 watchdog 建立是控制流候选，未建立本次因果证据，未据此改代码。
当天20:02的 pipeline_stages 唯一约束错误属于另一路；不能当作飞书数据库失联原因。

## 恢复操作

通过官方公司配置 POST 原样重新应用当前 `configJson`，没有更换机器人、模型、路由或会话。
执行前后 configJson SHA256 均为 `421aeb210dd86fb2983a6e0fc8514f99a2e846664ee05b45eef05c8829a2a8ae`。
Paperclip 主进程与启动时间保持；23:38:29 原公司配置已应用，唯一订阅器PID2815276建立，UID1000。
原插件内部30秒恢复检查已经推进，23:40:29回读 lastWatchdogAt=15:40:29Z。
该 status 桥回读属于有副作用的恢复检查；初始缺失证据先用进程和只读 catalog 保留。
旧 Python CM、已退役 cron 与其他服务器未参与恢复。

## 新消息实测

23:39:20 合成源 `om_x100b63d1444de0a8ce4c868d370d7bd` 发出，监听实际记录收件。
原生 issue `7507f19d-8a04-41f5-ac68-9c1e6d549e59`；源评论 `9d78027e-619a-4195-9253-d9ec138cc2fc`。
运行 `9e2e9e5c-e90c-463a-bce0-adedd95bd47f` 于15:40:14Z succeeded/exit0。
23:40 原机器人主聊天回复“436监听恢复验收通过”，ACK `om_x100b63d140eb10a0c1f0b8c27f8e1c2`。
本机 user CLI 平台独立回读原 App、非空正确内容、thread为空，最新列表中该源只有一个回复。
此次确认恢复后的接收、执行和送达；不从该短回复推断公众号或网站业务验收。

## 原消息接续

以436自己的 cm436 bot GET原23:25消息，核对原 MessageId、聊天、user/open_id 与 native owner一致。
正文2215字符，只在同一进程内传递，不落盘、不打印；没有复制本机另一个 App 的 OpenID。
经既有 authenticated `simulate-inbound-message` 动作一次补入，保持原 MessageId/发送者/聊天。
省略 retryIssueId、伪造 eventId 和 threadId，沿 native/legacy 去重与原生队列。
返回 ok=true、nativeConversation=true、status=submitted，仍归原 issue。
独立回读恰好一条原源评论 `bac174b1-2fb1-4eb3-92f3-07646a12587b`，clientRequestId `3519447b-b3b4-5809-8a69-78d6fa735e90`；正文字符数及SHA与436平台原源一致。
运行 `2bb35fd4-dd8e-4db8-96a0-3ddabc1a36aa` 于23:43:14启动，原生队列正常执行；sessionBefore沿用刚验收的提供商会话。
23:46:17仍 running，无持久最终评论或ACK。原消息交付仍待回读，不把补入或运行中报告为完成。

## 防止重复遗漏

构建/版本、配置落库、worker应用配置、唯一订阅器、原生运行、飞书实际回复分别验收。
升级后的 worker 未建立公司上下文时，保留缺失现场，再原样应用已核对的原配置。
不盲目重启主服务、替换身份或换模型。未知消息沿原 ID 对账，不能自动生成第二个源任务。
操作步骤已写回 [插件说明](../../../plugins/feishu-connector/README.md) 与 Ops 436 操作手册。

知识收尾 already_covered：沿用 Wiki「远端任务恢复：先确认提交边界」「诊断信息：保留代码位置和必要计数」「按当前任务选择验收依据」。
根 Codex 负责本轮原消息交付与文档收口；宿主回放具体失败点仍为未确定，不扩展成新调度/巡检机制。

## 原任务后续状态

23:53:28，原运行 `2bb35fd4-dd8e-4db8-96a0-3ddabc1a36aa` 以 timed_out/exit143/errorCode=timeout结束。
23:54:08，Paperclip 自动创建原生接续 `e3c53fc2-a451-47f1-8da5-8f3074a98bb4`。
完整 context 显示 wakeReason=transient_failure_retry、retryOfRunId为前述原运行、wakeCommentId为同一源评论；invocationSource=automation、triggerDetail=system。
根 Codex 没有第二次投递或启动新源。原生 CLI 按最新关联运行返回 pending，未把旧超时当作当前运行的最终回复。
23:57回读该接续仍 running。业务任务暂无最终评论或实际答复；不能将合成验收成功提升为原任务完成。
接续 owner为原436 CM Agent与Paperclip原生队列。根 Codex负责恢复边界的独立复核；不在本次收件恢复中反复投递原任务或改模型/运行预算。

本批普通文档本地链接与diff检查通过。Ops完整pre-commit的11个hook通过，更新既有436手册后重新生成两份既有索引。
CM/Ops恢复材料已分别提交推送，远端main回读一致；本次补记仅修正原任务状态，不改变运行策略。
