# 飞书接入 Paperclip 持续对话

## Goal
飞书私聊复用 Paperclip 原生持续对话。具体工作使用独立执行任务；原机器人身份、现有任务和有效定时任务保留。

## Scope
修改外部飞书插件及必要的薄适配。Paperclip 核心保持原样。先在本地验证，再选择 436 部署；不批量覆盖服务器，不恢复 meiren 的 CM。

## Acceptance
- 同一用户与 Agent 的普通私聊连续，不依赖回复旧消息。
- 原生 conversation 与执行任务分开；完成任务后仍能接新需求。
- 身份、公司、Agent、原消息回执绑定明确；重复事件不重复派发或回复。
- 重启后可恢复，明确重置后旧运行不能污染新上下文。
- 群话题和既有任务线程保留原行为。
- 离线及隔离真实 Paperclip 验证通过；生产消息验收单独记录。

## Plan
1. 核对插件源码、原生 conversation/channel 接口及授权边界。（completed）
2. 实现可复现构建与显式持续私聊入口。（completed）
3. 验证连续对话、去重、隔离与恢复；明确独立任务及卡片边界。（completed）
4. 独立审查、受控部署、更新交接并提交推送。（completed）

## Next Step
本机和 436 真实连续私聊、源码及 Ops 交接已验收交付。交互卡和执行任务主管唤醒按独立需求接续，不机械扩建。

## Adopted Knowledge
- CM 是薄适配，Paperclip 负责生命周期；不增加第二个调度器。
- 代码验证与真实交付分别判断。来源：Obsidian `Wiki/自动化开发范式与智能体协作.md`、SpecMesh v1.1。
