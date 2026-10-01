# Progress

## Current
会审 v1 薄适配实现与本机无模型原生协议验收完成，准备提交推送。不是供应商模型效果、成本硬上限或跨机恢复验收。

## Done
- 定位指定会审的原文和已提交摘要；只审查流程，不重评技术路线。
- 新增 `scripts/paperclip/cm-consult`；薄入口 `cm-paperclip consult` 路由同一脚本。本机独立 `cm-consult` 链接可用，旧 Python cm 未替换。
- 冻结输入/初判，两个独立咨询槽和唯一补充槽；原生 child/blockers/事件，无后台循环。创建结果不明时保留槽位，不自动再次创建；可严格绑定原 Issue。
- 评论按 company/parent/agent/brief/revision/slot/run 归属核验；新 run 后拒绝旧结果，冲突重报拒绝；partial/失败/取消不冒充完整意见。未知计数保留 null，仅统计提交包计数齐全度，非整场账单。
- 裁决引用当前原生证据摘要，保留分歧和下一步，不自动发布、不自动完成父任务、不写其他项目代码或记忆。

## Verification
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --confcutdir=tests/paperclip_adapters tests/paperclip_adapters`：129 passed、12 subtests passed（含新增22项）。
- 正常仓库测试入口 `uv run pytest -q tests/paperclip_adapters`：129 passed、12 subtests passed（5.14s），不是仅绕过根配置的专项结果。
- 本次文档新增/修改区域的9个本地链接均存在；未扩展为历史全仓链接修复。
- `uv run ruff check scripts/paperclip/cm-consult tests/paperclip_adapters/test_cm_consult.py tests/paperclip_adapters/consult_native_probe.py`：通过；shell `sh -n scripts/paperclip/cm-paperclip` 和 diff 空白检查通过。
- 本机 Paperclip 2026.916.1，独立测试公司 `6896e6ce-c9c3-47c7-9a48-b251992581f5`，父 Issue `34d8f4ed-b3ab-49b3-a5a7-871b5e6f13f8`。只创建三个确定性 process Agent，零模型请求，未改既有公司或服务器。
- 第一次真实创建暴露 children 响应形状错误；修正后用 bind 恢复同一个 backlog 子项，再派发另一子项，无重复创建。
- 两个 worker run `4babdaae-6a8f-4a3c-a3b7-972730c5eaf6`、`d0ebc97f-4c1c-4fb6-9730-f0587ccc4022` 均 succeeded，评论与归属独立读回；真实 CLI collect 为 ready=true、reported_usage_complete=false。私有证据仅保存在本机数据盘 acceptance 下，未入库。
- 父 run `be739d3b-e1e8-4544-98de-df726f13d7c1` 的 wakeReason 为 issue_children_completed；随后原生追加 finish_successful_run_handoff。两次均 succeeded；不能据此保证单次唤醒。三个测试 Agent 已暂停，测试公司/任务保留审计，不删除。
- 本轮未运行全仓旧 runtime 测试、未改 Schema/SDK/Web、未运行真实模型或重新测试 SO101；新增测试由现有 `pytest -q` CI 自动发现，原生探针仅显式调用。

## Remaining
- 在用户下一次真实关键决策中验收所选模型的结构化回报、timeout/恢复及最终建议质量；不为凑验收重复已完成的领域咨询。

## Issues
本轮不得以 mock/离线测试声称真实多模型、原生唤醒或成本封顶已验收。
已补原生无模型唤醒证据；仍不证明真实协调模型在每种恢复路径都只调用一次。共享私有目录不是 worker 安全沙箱，用户级权限与预算由原生 Agent 配置负责。
既有遗留：Orca/cron 按 repository-closeout-policy/progress.md 移交根 Codex；436 bootstrap 不作为部署入口；tau-bench/experiments/.gitignore 已由该任务报告提交到独立 codex/tau-bench-20261001 分支（888639a），此处保留本地副本，不未经差异审查再并入 main。根 Codex 接续入口为其 progress.md 与 experiments/tau-bench/README.md，先核对分支等价与原始材料忽略范围。

## Next
完成当前交付后只在真实关键决策按需使用；不自动启动咨询、不恢复旧 Orca 队列。
