# Progress

## Current
2026-10-01：CM 使用 Paperclip 底座与薄适配，不修改上游核心。[全服务器迭代](../fleet-paperclip-agy-20261001/progress.md)已接受：8 台默认 cm/controlmesh 绑定各机独立 context/company，63 项有效 CM 定时任务转为 native active schedule；新服务持久启动，旧消费者停止。8 台 AGY 1.2.14 程序更新接受，各机不同账号，用户选择登录后置。

436 的默认 cm/controlmesh 与飞书消费者已迁移，旧 Python CM 停止并禁用，公众号 timer 保留。用户确认公众号协作用于日常产出、网站入口有进展；内容 QA、真实消息与运行时分别验收。436 post 消息复测状态见[对应进度](../436-paperclip-feishu/progress.md)。

bf2025 原有只读 cron CMB-7 经原 Claude/sonnet 真执行后 done/succeeded/exit0；另六台各一次无模型指标任务由根直接回读本轮产物与原生回执。BF14、greenrise12、colocrossing16、Moonrise21 的原时刻/时区和静默/业务策略保留；原停用任务、OS cron/timer、身份/config 不丢失。薄适配 107 项测试及 12 项参数化子测试通过，代码已推送。

全机只用飞书，Telegram 可停但身份/config 保留。bf2025、436 有各自既有飞书身份，其余 6 台缺自己的绑定。正常运维静默，业务产物和待投递状态保留；执行前方向核对仍为[已记录待选用需求](task_plan.md)，不自动新增模块。

## Done
- 2026-10-01：用 TraceMesh 复盘公众号、网站与模型交接，记录批量前的最小改进；纠正“产品集成/生产切换都未完成”的过宽描述，保留 436 post 复测、内容 QA 和其他主机的独立边界。8 份交付文档与 58 个相对链接检查通过，既有未接受实现仍由根 Codex 按原交接接续。
- 2026-10-01：将“CM 是概念与薄适配层，Paperclip 是实际运行底座”前置至 AGENTS、README、PROJECT；同步决策与计划，不变更运行时代码或部署状态。
  验证：`git diff --check` 通过；新增本地链接目标均由 Git 跟踪，`CLAUDE.md` 仍引用 AGENTS；人工审查交付 diff，无凭据或运行日志。仅文档变更，未运行模型或代码测试。既有未提交 Orca/cron 与 436 部署记录保持原貌，继续按下方 Issues 的 owner/入口交接，不冒充已验收成果。
- 真实Codex派发三个CLI，结束推理，三份结果后事件唤醒并独立审批。
- AGY/CBC被接受；ZCode经一次纠偏仍被拒绝，原始结果保留。
- 更新当前入口和取代关系；保留Orca候选、旧任务与既有未提交改动。
- 已复用社区连接器完成兼容修正与默认去噪；用户两条真实消息验证已有机器人收件、Agent 执行和原会话回复。

- 初始方向记录曾完成 CM/CapMesh 文档检查；后续真实 CLI 与飞书试验、此次收尾分别记录在对应计划，不能沿用初始“未运行模型任务或产品测试”的边界。

## Remaining
436 的 post 消息复测、六台独立飞书绑定、各机 AGY 登录、运维风险判读/异常投递与业务外部目标分别接续；既有 CLI/63 个 schedule 的接管已经接受，不重复做候选部署。不要求 Telegram HTTPS。

执行前方向核对保持“待选用”，范围、采用/停止条件见 task_plan；不自动进入实施队列。

## Issues
已接受的本机文本链与服务器 CLI/调度接管不代表附件、完整群聊策略、各机飞书投递或全部业务发布通过。greenrise 历史 canary 阻碍不再用于否认本轮已完成的 headless 接管。

436 当前由根 Codex 整合接管，状态回源到其 task_plan/progress。既有 Orca 与 cron 遗留继续按 repository-closeout-policy/progress.md 交接给根 Codex。

## Next
登录和缺失飞书绑定按用户安排接续；436 有新消息时补待验收项，无新消息不持续盯守。根串行交付状态，并用既有收尾 CLI 将 Current 同步 CapMesh；不新增 Actions/cron/常驻 Agent，不重复已接受的模型或文本试验。
