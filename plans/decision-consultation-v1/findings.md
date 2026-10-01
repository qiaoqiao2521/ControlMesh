# Findings

## Source
SO101 `plans/colab-digital-twin-20261001/learning-review.md`（交付 de7d17b）；Codex 会话 `01a0f3c6-1945-70c0-9fb8-e3566997bb62`，turn `01a0f655-ae37-7013-9761-a26649fdfa3d`，用户消息 `01a0f655-aeb8-7fb1-bd85-d21257d7a243`。已用 app 定点阅读原用户要求、咨询活动及最终答复，不复制原始日志。
TraceMesh 首次缓存精确搜索为空，freshness unknown；明确刷新后再查，不把旧缓存零命中当不存在。
刷新后用 `ARM101` 命中上述 session（第一页5条、has_more=true；定位目标后停止扩展）。index_revision `d16d0c0ac5a160974e80ccd1a7021cc34ee6f47a2afcd2c1dab4f09a67434ef3`。最新会审正文由 app 对选定 turn 展开，未以搜索片段代替全文。

## Process audit
- 已做到初判冻结、实质分歧保留、引用与实测分开；不是多数投票。
- 该会审直接调用 CLI，文档明确未验收 Paperclip 调度/恢复。
- AGY 首轮 partial，ZCode 首轮空正文超时；补取和定向复核是不同目的但都花一次调用，应共用预声明额度。
- 用量部分未知；不能用最后成功请求的 token 当整场总费用。
- 原始材料已 Git 忽略，正式决策只保留必要摘要和引用。

## Existing boundary
本机原生协议测试发现旧 bridge 的 `result.issue` 假设不能直接复用：2026.916.1 children 路由返回 issue 本体。已修正新适配与 fixture；首次创建的 backlog 子项保留，未再盲目重试。测试 Agent 已暂停。
原生 process adapter 不保证提供 PAPERCLIP_TASK_ID；通过真实 run 的 contextSnapshot.issueId 验证，若环境显式提供 task ID 则必须一致，未伪造环境。原生 issue runs 列表使用 runId，详细 run 使用 id。
实际父任务有 issue_children_completed 和 finish_successful_run_handoff 两次唤醒；不能宣传恰好一次模型运行。CM 重复 dispatch 不重新放行，裁决固定证据版本；额外原生唤醒的调度仍归上游。
CapMesh PIT-002 用于限制接口范围：只接当前 children/comments/run，未复制通用 SDK 或 provider 启动器。
复用 scripts/paperclip/cm-paperclip 入口；历史 bridge.py 已用上游 POST /issues/:id/children + blockParentUntilDone。旧领域 worker 与 cron runner 不作为新调度器。
采用既有知识页“按当前任务选择验收依据”：派发成功、回复完整、证据有效、决策接受四项分开。

## Preserved work
基线有旧 Orca 接线/测试、cron 提案、436 bootstrap、.gitignore 与 tau-bench/experiments 进行中材料；不覆盖。原 owner/验证入口见 repository-closeout-policy/progress.md 与 tau-bench-20261001，根 Codex 接续未验收项。
