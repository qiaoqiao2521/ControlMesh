# Progress

## Current
2026-09-30：CM 基于 Paperclip 的方向已确认，CLI 协调与独立审批、本机飞书文本闭环已验收。4GB greenrise 替换试验已结束：候选服务停止并禁用自启，保留原 CM 入口。具体通过项和生产接管阻碍见[飞书 canary 状态](../paperclip-feishu-canary/progress.md)。

用户进一步确认保持 Paperclip 上游源码不动，最多增加薄外部编排。执行前方向核对已作为真实需求记录，尚未实施；无法低成本复用时可以不加入。

## Done
- 真实Codex派发三个CLI，结束推理，三份结果后事件唤醒并独立审批。
- AGY/CBC被接受；ZCode经一次纠偏仍被拒绝，原始结果保留。
- 更新当前入口和取代关系；保留Orca候选、旧任务与既有未提交改动。
- 已复用社区连接器完成兼容修正与默认去噪；用户两条真实消息验证已有机器人收件、Agent 执行和原会话回复。

- 初始方向记录曾完成 CM/CapMesh 文档检查；后续真实 CLI 与飞书试验、此次收尾分别记录在对应计划，不能沿用初始“未运行模型任务或产品测试”的边界。

## Remaining
可复用 CLI 适配归位；按真实任务选择群聊与恢复语义；服务器接管前解决 HTTPS、CLI/provider 可用性和 cron 迁移。

执行前方向核对保持“待选用”，范围、采用/停止条件见 task_plan；不自动进入实施队列。

## Issues
本机文本闭环通过不代表附件、完整群聊策略、多机或生产迁移通过。greenrise 当前没有接管旧 CM。

本轮仅更新需求/约束记录。并行的 `plans/436-paperclip-feishu/` 仍在准备接管，由原部署任务负责，未代为提交未完成的现场记录；接续入口是其 task_plan/progress。既有 Orca 与 cron 遗留继续按 repository-closeout-policy/progress.md 交接给根 Codex。

## Next
继续工作时按已选真实任务确定群聊/恢复验收，或先修复选定服务器 CLI 的非交互交付能力。当前不自动重开服务器试验，不重复已通过的本机文本验收。
