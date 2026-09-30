# Progress

## Current
2026-10-01：用户确认公众号协作已用于日常产出，网站底层与 Agent 使用入口已有进展。TraceMesh 复盘已形成[迁移优化与 10 月 2 日批量接续](../436-paperclip-feishu/migration-review-20261001.md)：先让一台新增主机交付真实任务，再逐机复制；复用程序，保留各机身份、模型默认与有效 cron。本轮未执行新部署，文章内容 QA、飞书特定消息复测与运行时迁移分别判断。

2026-10-01：436 默认 cm/controlmesh 与飞书消费者已切换到 Paperclip；旧 Python CM 停止并禁用自启。Telegram 停用但保留身份/config，公众号 timer 与 cron 调度保留，运维通知改飞书且无异常静默。首次真实 post 消息发现空正文，修复后等待复测；详见[436 验收状态](../436-paperclip-feishu/progress.md)和[命令入口](../../docs/paperclip-436.md)。这不代表本机和其余服务器已迁移。

2026-09-30：CM 基于 Paperclip 的方向已确认，CLI 协调与独立审批、本机飞书文本闭环已验收。4GB greenrise 替换试验已结束：候选服务停止并禁用自启，保留原 CM 入口。具体通过项和生产接管阻碍见[飞书 canary 状态](../paperclip-feishu-canary/progress.md)。

用户进一步确认保持 Paperclip 上游源码不动，最多增加薄外部编排。执行前方向核对已作为真实需求记录，尚未实施；无法低成本复用时可以不加入。

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
436 薄 CLI 与输出/飞书适配已归位，真实消息复测待完成；之后按主机分别迁移入口与有效 cron，按真实任务选择群聊与恢复语义。greenrise 原有阻碍保留；436 只用飞书，不再要求 Telegram HTTPS。

执行前方向核对保持“待选用”，范围、采用/停止条件见 task_plan；不自动进入实施队列。

## Issues
本机文本闭环通过不代表附件、完整群聊策略、多机或生产迁移通过。greenrise 当前没有接管旧 CM。

436 当前由根 Codex 整合接管，状态回源到其 task_plan/progress。既有 Orca 与 cron 遗留继续按 repository-closeout-policy/progress.md 交接给根 Codex。

## Next
10 月 2 日按迁移复盘逐机接续；436 有新消息时补待验收项，无新消息不持续盯守。不重复已通过的本机文本验收，不把 greenrise 的历史停用状态套用到 436。
