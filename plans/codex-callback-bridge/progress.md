# Progress

## Current

2026-10-11：只接本机。QIA-99 真实结果补发已通过。QIA-100 新任务的原生派发 → 完成事件 → queue → 原会话自动接续 → 文件独立核验闭环已通过。研究草稿需要修订，原生 issue 保持 in_review；本次一次性 Agent 已暂停并读回确认。

## Done

- 固定 codex_callback commit 5193e2ece5caf2ac1805800575e5567a972f657c，保留 MIT、来源与文件哈希。仅对 queue/start 消费竞态补历史回执对账。
- 实现 bind/notify/status；绑定原线程与同 daemon，对外部 run 去重。创建结果未知时保留事实，pending 文件不能单独证明 worker 已启动。queued/started 不能当作业务验收。
- 安装本机 cm-codex-callback 入口。未替换旧 cm，也未将 436 模板安装为本机 Paperclip。
- 安装后的适配代码只读预检通过：原线程与 cwd 匹配，服务版本 0.162.1；queue 写入为 0。原 idle/busy 验收记录原貌保留，无第三个 callback，无 App 切换。
- 36 项隔离测试通过：9 项上游 DeliveryTests、5 项消费竞态测试、22 项适配行为测试。未运行真实 worker、ProcessTests 或 live_test。
- 两份新增测试通过 Ruff；入口通过 E/F 检查（忽略动态 runtime import 的 E402）、语法检查和已安装命令 help。该结果不代表入口通过全部 Ruff 规则。
- 使用说明与架构、决策、计划索引已更新。
- 11 项来源/补丁/测试哈希、183 个本地文档链接与暂存 diff 检查通过。23 个提交文件经范围检查，无运行状态文件和凭据模式命中；使用已验证的新账户推送到既有目标仓库。
- QIA-99 补发：原线程 active 时仅一条 matching queue 消息；随后 status=started、receipt_source=history。持久历史仅一个匹配 client ID/marker/交接路径的 turn，queue 已无该消息；实际 CODEX_THREAD_ID、queue_id、turn_id 对账通过。交接文件、批回执与五份产物哈希读回一致，私有 acceptance.json 已保存并读回。不宣称当前核验 turn 已结束。
- Native heartbeat succeeded/exitCode=0，原生任务仍 in_review、批回执 held。N011 终审通过，N012 待修订。社区外部通知没有 command，其 returncode=null 合乎 notify() 行为，不代替原生退出证据。
- 新增单任务 native event watcher 与单轮研究 worker；12 项 Node 事件/身份/终态/退出码/产物篡改测试通过。Node 语法检查、worker E/F 与 help 检查通过；未重跑原两事件验收。
- QIA-100 先创建 backlog、绑定原会话、验订阅就绪，再切 todo 原生派发。读回 in_progress 与 run=running；worker-attempt 保留记录已存在，watch 无错误。具体 UUID、PID、模型日志与运行状态仅保存在 Night Lab 忽略的 .runtime/codex-callback/local-model-deployment-20261011/。
- QIA-100 后续 native status=succeeded/exitCode=0、issue=in_review、草稿已生成。watch 收到 heartbeat.run.status 终态事件，重新核验 run/task/agent/link、worker 与三份产物哈希后自动 notify。队列中仅一个匹配 callback，原线程仍 active；queued-evidence.json 私有保存。本轮没有手动执行 notify 或轮询来触发通知。
- QIA-100 原会话自动接续后，实测 CODEX_THREAD_ID 与绑定原线程一致。持久历史只有一个匹配 callback/client ID 的 turn；marker、交接路径与哈希、queue_id、turn_id 均对账通过，队列匹配项已为零。handoff、worker 回执、三份产物与研究事件文件哈希读回一致。acceptance.json 私有保存并读回，不提前宣称当前核验 turn 已结束。
- 六个研究来源均有 completed webfetch，模型最终 reason=stop、exit_code=0。原会话另读官方 Linux/build/server/FAQ/context 文档，发现构建命令缺目录参数、AMD 安装边界过宽、KV 量化条件缺失、通用内存公式与维护成本概括证据不足。operator-review.json、review.md 私有保存；原产物不改写，业务接受保持 false，没有重跑模型或安装本地模型。
- 通过原生 pause 接口仅暂停本次一次性 Agent，并重新读回 paused。原生 run 仍 succeeded，issue 仍 in_review，保留审计与待审交互；没有创建或发送另一条 callback。
- 用户后续要求把君临天下项目返工接到 queue。QIA-101 已独立绑定、订阅就绪后派发；其项目 worker 的动态模块缺 __file__，在启动 AGY 前失败，原生 failed 事件已通知 queue。离线复现与标准模块加载修复后，复用子进程入口 /usr/bin/true 回归通过；QIA-102 按父子任务保留失败并重新绑定、先订阅后派发，旧 Agent 已暂停，旧 callback 不重发。新增可选 spec.followup 仅描述任务自己的验收入口，原生身份和社区传输不变。产品返工与验收属于游戏工程计划；不将派发说成产品完成。运行证据继续私有保存，历史遗留仍保留。

验证命令（仓库根目录）：

```sh
env PYTHONPATH="$PWD/vendor/codex_callback/runtime:$PWD/vendor/codex_callback/tests:$PWD/tests/paperclip_adapters" \
  PYTHONDONTWRITEBYTECODE=1 python3 -B -S -m unittest \
  test_callback.DeliveryTests test_codex_callback_delivery.DeliveryRaceTests test_cm_codex_callback.BridgeTests
```

## Remaining

- QIA-100 回传验证已结束。草稿修订仍待独立研究任务，不自动重试收费阶段。根 Codex 为待审接续 owner；最短入口为本次私有目录 review.md 与 operator-review.json。
- 该订阅仅覆盖本次明确绑定任务，不代表所有后续 CM 任务已经自动绑定，也不代表断线恢复或长期后台服务通过。
- App 下次普通启动的持久连接仍需独立验收。

## Issues

本机没有 Paperclip CLI 不代表没有运行实例。沿 Night Lab 的 cm.json 核实本机 127.0.0.1:3100 已运行 Paperclip 2026.916.1，qiao 公司及最新 run 可读回。QIA-99 是已有结果补发；QIA-100 已验通真实原生完成事件的单任务回传。所有后续任务自动绑定与持续服务仍未验收。跨主机传输不属于当前范围。

开工遗留的 Orca、未接受 cron 提案及历史部署材料继续保留；具体阻碍与最短接续入口见 [Handover & Retained Legacy](../repository-closeout-policy/progress.md#handover--retained-legacy-移交根-codex-独立审批与接续)。接续 owner 为根 Codex，不将未接受成果混入本次提交。

## Next

本次闭环验收停止，不重复派发或重跑模型。未来新任务沿既有 bind → 订阅就绪 → 原生派发 → 完成事件 notify → 原会话独立验收的顺序。业务待审与传输回执分别记录；本次草稿修订要求已交接给根 Codex。

## Knowledge closeout

already_covered：采用 Obsidian Wiki/自动化开发范式与智能体协作.md 的“远端任务恢复：先确认提交边界”，保留未知提交结果并先对账，避免重复触发。CapMesh 的复用原则也已覆盖本次选择。社区竞态补丁与具体命令保留在本项目，无需重复创建共享知识页。
