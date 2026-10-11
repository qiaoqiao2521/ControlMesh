# Findings

- 2026-10-11 用户明确选用 codex_callback，非 wake-codex。社区代码固定 commit 5193e2ece5caf2ac1805800575e5567a972f657c；notify() 不接管 CM 执行。
- notify() 每次生成新 UUID，外部重复事件需要在调用边界去重。采用单 run 私有目录和 OS 文件锁，保存调用前保留记录；结果未知时先对账已有目录，不能重新调用 notify()。
- 历史两事件验收已通过；原 reference 不改动。新 runtime 放 vendor/codex_callback，许可和最小 patch 单独标明。
- 当前只读预检：服务 0.162.1，原线程已 loaded，cwd 匹配，允许直接输入且 active。内核 socket peer 证明 App 与该 daemon 相连。未发送消息；实际线程 ID 与运行记录仅保留在私有本地验收目录。
- cm-paperclip 只透传原生派发；cm-agy 与 cm-process-runner 保存 handoff 后更新原生 issue。当前没有已证实的 CM→本机 Codex 完成事件回传通道；飞书属于独立路线。
- 本机 PATH 中 cm/controlmesh 仍是旧 uv 工具包，未发现 paperclip/paperclip436 命令。cm-paperclip 固定的是 436 专属 context。因此提供独立本机入口，不把这份远端模板安装为本机默认 cm。
- 后续用户授权即时试用：沿 Night Lab/cm.json 发现并读回本机 127.0.0.1:3100 Paperclip 2026.916.1；缺 CLI 不能推断实例不存在。最新 QIA-99 的 native run succeeded，但批回执 held、issue in_review；N011 通过，N012 待审。原生评论与批回执、卡片、晨报、catalog、终审事件哈希一致。本次仅补发已有结果，不重复收费执行，不安装新调度。
- QIA-99 已真实回到原 Codex 会话；status=started 的 history 收据与本轮持久 userMessage.clientId/marker 匹配。外部 notify 不执行命令，因此消息 exit code=None 不是 CM 执行失败；真实 Paperclip heartbeat 的 exitCode=0 单独核对。补发记录私有保存，不把未来完成钩子或业务待审描述为通过。
- QIA-100 复用本机 Paperclip 原生 company live events。已安装源码 realtime/live-events-ws.js 验出 events/ws 路径；services/heartbeat-run-status-payload.js 与 heartbeat.js 验出 heartbeat.run.status 在写入终态后发送。新增单任务外部订阅，直接使用 Node 内置 WebSocket 与现有 notify；不重建传输、调度或模型执行器。订阅先就绪，再将 backlog 切 todo 原生派发，避免快速完成事件遗漏。
- 研究复用 Night Lab run.invoke/validate_research/verify_access，只执行 GLM 研究一阶段。使用独立私有任务目录与 native process Agent，不修改现有 Night Lab 日程、队列或失败题。初次启动订阅时错误指定不存在的 /usr/bin/node，OS 返回 ENOENT，未创建进程且未派发任务；保留事实后改用已核实 PATH 入口，就绪后才派发。
- 同 daemon 与回执要求采用已有 queue acceptance 的经验；原任务和原线程分别绑定，queue 入队不等于任务验收。
- 采用已有知识：CapMesh inventory/community-alternatives.md 与 pitfalls/002-upstream-protocol-wrapping-blackhole.md 的复用原则；用于保留社区客户端和原生生命周期，不编写通用协议包装层。

## Existing work

用户纠正先接 436 的选择，最新明确只接本机。未建立远程连接、修改远端配置或投递生产事件。

开工 Git 变动为 .gitignore、旧 CLI 接线、未跟踪 Orca 桥接/探针/测试、cron 提案、436 历史 bootstrap、experiments 与 tau-bench 等。当前已查 plans/repository-closeout-policy/progress.md 的既有分类/阻碍；原范围仍保留，不将未接受历史实现并入此次 callback 发布。接续 owner 为根 Codex，最短入口为该计划的 Handover & Retained Legacy。
