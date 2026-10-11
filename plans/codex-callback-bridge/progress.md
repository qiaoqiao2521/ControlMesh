# Progress

## Current

2026-10-11：只接本机。实现提交 c42900e 已推送并验远端。用户随后授权立即试用，当前准备以 Night Lab 最新已结束批次 QIA-99 补发完成通知；不重跑研究，不操作 436。queue 与实际接续仍须由本次运行记录核验。

## Done

- 固定 codex_callback commit 5193e2ece5caf2ac1805800575e5567a972f657c，保留 MIT、来源与文件哈希。仅对 queue/start 消费竞态补历史回执对账。
- 实现 bind/notify/status；绑定原线程与同 daemon，对外部 run 去重。创建结果未知时保留事实，pending 文件不能单独证明 worker 已启动。queued/started 不能当作业务验收。
- 安装本机 cm-codex-callback 入口。未替换旧 cm，也未将 436 模板安装为本机 Paperclip。
- 安装后的适配代码只读预检通过：原线程与 cwd 匹配，服务版本 0.162.1；queue 写入为 0。原 idle/busy 验收记录原貌保留，无第三个 callback，无 App 切换。
- 36 项隔离测试通过：9 项上游 DeliveryTests、5 项消费竞态测试、22 项适配行为测试。未运行真实 worker、ProcessTests 或 live_test。
- 两份新增测试通过 Ruff；入口通过 E/F 检查（忽略动态 runtime import 的 E402）、语法检查和已安装命令 help。该结果不代表入口通过全部 Ruff 规则。
- 使用说明与架构、决策、计划索引已更新。
- 11 项来源/补丁/测试哈希、183 个本地文档链接与暂存 diff 检查通过。23 个提交文件经范围检查，无运行状态文件和凭据模式命中；使用已验证的新账户推送到既有目标仓库。

验证命令（仓库根目录）：

```sh
env PYTHONPATH="$PWD/vendor/codex_callback/runtime:$PWD/vendor/codex_callback/tests:$PWD/tests/paperclip_adapters" \
  PYTHONDONTWRITEBYTECODE=1 python3 -B -S -m unittest \
  test_callback.DeliveryTests test_codex_callback_delivery.DeliveryRaceTests test_cm_codex_callback.BridgeTests
```

## Remaining

- 真实本机任务使用原生 company/issue/run 绑定后，由其完成钩子调用 notify；真实任务回传需单独验收。本轮不制造额外事件来替代该验收。
- App 下次普通启动的持久连接仍需独立验收。

## Issues

本机没有 Paperclip CLI 不代表没有运行实例。沿 Night Lab 的 cm.json 核实本机 127.0.0.1:3100 已运行 Paperclip 2026.916.1，qiao 公司及最新 run 可读回。此前“未发现完成钩子”边界仍成立；本次是已有任务结果补发，不能称为已安装持续完成回传。跨主机传输不属于当前范围。

开工遗留的 Orca、未接受 cron 提案及历史部署材料继续保留；具体阻碍与最短接续入口见 [Handover & Retained Legacy](../repository-closeout-policy/progress.md#handover--retained-legacy-移交根-codex-独立审批与接续)。接续 owner 为根 Codex，不将未接受成果混入本次提交。

## Next

根 Codex 核验 QIA-99 补发的 queue/turn 与交接文件回读；具体证据只存 Night Lab 被忽略的私有 runtime。后续持续回传仍应接既有完成钩子，不重建调度器。

## Knowledge closeout

already_covered：采用 Obsidian Wiki/自动化开发范式与智能体协作.md 的“远端任务恢复：先确认提交边界”，保留未知提交结果并先对账，避免重复触发。CapMesh 的复用原则也已覆盖本次选择。社区竞态补丁与具体命令保留在本项目，无需重复创建共享知识页。
