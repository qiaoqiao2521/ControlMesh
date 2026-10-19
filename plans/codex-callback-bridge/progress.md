# Progress

## Current

2026-10-20 最新决定：CM 专注同一 Harness 内的多 Agent、多模型／多 Runtime 协作；增加 MACPIE 模型统筹职责，具体项目与接入待确认。以后不研究跨 Harness 编排，不建设多厂商 Agent Runtime 平台。hcom 跨 Harness 接入移出后续计划，acpx／统一 ACP 继续停止。原因与取代范围见[最新决策](../../docs/DECISIONS.md#2026-10-20--单-harness-协作与模型统筹)。本轮仅记录、同步与交付，没有安装、配置变更、任务派发或服务迁移。

以下为历史验收与保留边界，不是继续扩展跨 Harness 的任务清单。MCode 原生后台任务／完成通知仍可复用；Codex App 接收端保留 native queue。旧服务保持运行所有权。

2026-10-18 当时选定：用户选择 MCode 原生后台任务完成通知 + hcom 跨 Agent 消息协作。此选择中的 hcom 后续接入已被 2026-10-20 决定取代；当时没有安装或本机验收 hcom。

2026-10-18 后续授权：用户要求发起端也可互换，并批准一次 MCode → AGY → 原 MCode 会话实测。MCode 0.5.9 常驻 TUI 原生后台 Bash 派发一次 AGY，首轮结束且会话 idle 后，原生完成事件自动开启同会话新轮次。新轮调用 task_output 一次，回读产物、独立计算 SHA256，写出验收并正常完成；根 Codex 再核验持久化 task、两个 completed turn、delivered 回执、答案与哈希。没有追加用户提示、重新登录、安装适配器、恢复 acpx、重启 App 或投递 Codex callback。

最小使用方法：让发起 MCode 会话以原生 Bash 的 `run_in_background=true` 运行原 CLI 命令，保存实际 task_id 并结束派发轮；原生完成通知到达后用 task_output 读结果、独立验收。保持该 TUI 运行；当前版本 `mcode exec` 在单轮结束后关闭运行时，不能当作常驻接续入口。测试闸门仅控制任务结束时机，产品用法无需闸门或专用 wrapper。

私有证据位于本机 `Documents/Codex/2026-10-18/mcode-agy-native-acceptance/`，包括 idle-before-completion.json、acceptance.json 与 observer-verification.json；会话 UUID、原始日志和运行态不入库。已验收范围仅为 MCode 原生后台管理一次 AGY 进程的 idle 接续；busy、取消、关闭后恢复、AGY 发起、任意外部任务注入与 hcom 接收没有验收，不再以补齐跨 Harness 能力为后续目标。此证据不证明 AGY 已成为同一 Harness 的内置 Runtime。

2026-10-18：用户已放弃 acpx／统一 ACP 试验，理由是新增运行包和独立登录维护，当前本机方向回到通知层。决定已写入 AGENTS、PROJECT、DECISIONS 和回调说明。AGY ACP OAuth 超时后进程已结束，授权页已关闭；不再等待登录或执行本次 App 切换。没有模型提示、callback 或 App 重启。现有 CLI 认证与 Paperclip 运行所有权未改。

2026-10-12 准则继承修复：CM 项目入口明确复用与流程成本；新 callback 保存提示版本 2，提醒原会话重读当前项目，watcher 默认说明改为通用任务范围。38 项 Python、32 项 Node 隔离测试通过；不将提示出现宣称为 Agent 实际采用。共享工作区飞书六机任务与历史遗留保留，本次不操作服务器、投递真实 callback 或派发模型。

2026-10-12：只接本机。QIA-99 补发与 QIA-100 的原生派发 → 完成事件 → queue → 原会话接续 → 文件核验已通过。QIA-100 五项研究修订已独立复审接受，原生 issue=done 读回；原件保留，一次性 Agent 仍 paused。接受范围是官方资料研究，未安装模型。

新增 `cm-codex-task launch/reconcile` 组合既有绑定、就绪订阅、派发与去重通知；31 项 Node 测试通过。用 QIA-100 原运行实测终态对账，原 callback/status 完全一致，原 handoff 未改写，无重派发或新 callback。新 launch 的整体真实派发、长期服务与普通 App 重启仍未独立验收。来源见 [遗漏修复](../mesh-omissions-20261012/progress.md)。

## Done

- 2026-10-20：新方向写入 CM 的 README、AGENTS、PROJECT、架构、决策和现有计划；MACPIE 身份待确认，hcom 退为历史。CapMesh D024、能力表和 PIT-002 已读回；新增相对链接／锚点检查 CM 16 条、CapMesh 11 条通过，diff 检查通过。独立只读审查无内容阻碍，指出受管快照须在 CM 提交后用既有 closeout 同步。已按用户授权保存长期记忆更新；本轮只有文档与记忆变更。

- 2026-10-18 最终方向记录：同步 README、AGENTS、PROJECT、架构、决策、Codex 专用说明和现有计划；旧 Paperclip 总览明确保留部署范围并指向新选择。新增本地链接/锚点检查 CM 20 条、CapMesh 7 条通过，diff 检查通过。本轮无模型调用、安装、配置或服务变更。

- 2026-10-18 后续实测：MCode → AGY → 原 MCode 会话的 idle 闭环通过；AGY 启动一次、task_output 一次、追加用户提示为零。原生完成来源位于 ingress 的 input_metadata_json.source=background-task，数据库顶层 source 仍为 turn。原会话验收与根 Codex 独立回读均通过，原始证据私有保留。

- 2026-10-18：6 份方向／回调文档已读回；8 条新增相对链接与锚点、git diff --check 通过。停止的试验材料已标记用户放弃，三项 case 均禁止继续；OAuth 进程退出及授权页关闭已核验。没有为文档记录运行模型或线上回调测试。

- 2026-10-12：新提示写入社区 callback 私有状态；旧无版本事件继续按原文对账，状态查询不改事件，重放不升级或重发。未知版本拒绝；显式任务 followup 与既有 handoff 字节保留。70 项隔离测试、Python AST、入口与测试的 Ruff E/F（忽略 E402）、Node 语法和 62 个本地文档链接／锚点、diff 检查通过。独立代码审查无阻碍，指出的 SpecMesh 链接锚点已修正。
- 2026-10-12：根 Codex 按官方 Linux/build/server/FAQ/context 页面修复 C1/C2/C3/C4/takeaways；修订报告 SHA256 为 26f4c8bbfdf57783aa60c991cb634b10053c1df7ebbba1fe36113344b746240c。原四份产物和 handoff 哈希复算一致；revision-acceptance 与原生 done 读回私有保存。未收费重跑或安装模型。
- 2026-10-12：补齐本机启动与终态恢复入口，派发前独占落盘，响应未知不重发，恢复复用身份/产物/去重检查。QIA-100 原运行实测 result.replayed=true，前后完整 status 相同；只新增恢复回执，原交接不变。51 项 Python（36 项 callback、15 项 closeout）和 31 项 Node 测试通过。

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

- MACPIE 的具体项目身份待用户确认；本轮完成方向记录，不安装或接入未知组件。以下历史未验收项仅在维护已授权的原路径时按需查看，不形成跨 Harness 建设计划。
- 提示传递已隔离验证，实际 Agent 采用待下一项已有授权任务观察。协调 Agent 负责把目标项目选定准则、交付物和停止条件放入原生任务材料；启动器不会替外部 worker 生成 prompt。owner 根 Codex，最短入口为 docs/codex-callback.md 的准则继承与任务范围；不新增验证任务。
- QIA-100 研究修订已接受；原 requires_revision 记录作为历史保留，最新结果见私有 revision-acceptance.json 与 revision-native-readback.json。
- 入口与单个原运行对账已验收；新 launch 完整真实派发与长期后台服务仍需在下一个授权任务验收。owner 根 Codex，最短入口为 docs/codex-callback.md 的本机任务启动与恢复。
- App 下次普通启动的持久连接仍需独立验收。

## Issues

2026-10-20 遗留清单复核：本轮开工仍存在下列未提交候选，内容和运行验收没有重做。Orca 与 cron 提案仍为未最终接受的本地候选；sandpile 进度写已验收并 done，但仓库交付尚未完成；tau-bench 已在独立分支提交 888639ac，当前未跟踪副本不重复整合。work/ 与 .zcodeignore 尚缺完整归属分类，可能包含原始审查材料和运行状态。以上均保留原貌，接续 owner 根 Codex；最短入口为既有 repository-closeout-policy/progress.md、free-time-sandpile-qia73/progress.md、tau-bench-20261001/progress.md。其范围与验收证据不足以在本次方向记录中完成全仓交付，不直接 git add -A，也不宣称已收清；新决定也不授权删除历史实现。

本机没有 Paperclip CLI 不代表没有运行实例。沿 Night Lab 的 cm.json 核实本机 127.0.0.1:3100 已运行 Paperclip 2026.916.1，qiao 公司及最新 run 可读回。QIA-99 是已有结果补发；QIA-100 已验通真实原生完成事件的单任务回传。所有后续任务自动绑定与持续服务仍未验收。跨主机传输不属于当前范围。

开工遗留的 Orca、未接受 cron 提案及历史部署材料继续保留；具体阻碍与最短接续入口见 [Handover & Retained Legacy](../repository-closeout-policy/progress.md#handover--retained-legacy-移交根-codex-独立审批与接续)。接续 owner 为根 Codex，不将未接受成果混入本次提交。

2026-10-12 共享工作区的飞书插件与六机 SDK／归属修复仍在进行。已向同项目对话“提出难以回答的问题”（01a0e21d-aa34-76c0-918a-17c9aaa5d736）协调，本次在隔离 worktree 验证并只串行整合上述 callback 与文档文件。飞书成果由该对话继续验收交付；旧 CLI／Orca 等保留项仍按上述根 Codex 交接，不混入未核实运行态。

## Next

本轮方向记录已完成，按既有 Git／closeout 流程交付。后续多 Agent 任务采用单 Harness 原生能力，MACPIE 只承担模型统筹，身份未确认时不安装；不恢复 hcom 跨 Harness 接入、acpx 或多厂商 Agent Runtime 平台研究。已有回调的未知结果仍只对账原 run，原会话独立验收。

## Knowledge closeout

2026-10-20 updated：选型已写入并读回 CapMesh docs/DECISIONS.md D024、PROJECT、能力表；原有 PIT-002 新增“CM 补充：跨 Harness 适配的维护代价”，pitfalls/README.md 同步入口。明确这是用户当前工作流的取舍，保留历史证据与未验收状态。长期偏好更新已写入授权记忆目录并读回；本轮采用 Wiki 的验收依据准则，不将具体选型重复写入 Wiki。

2026-10-18 最终方向 updated：选型与取代范围已同步至 CapMesh 的 PROJECT、capabilities/index.md 和 docs/DECISIONS.md D022，并读回确认 MCode 原生后台完成通知 + hcom、hcom 未安装/未验收的边界；D016 标记被取代范围，既有部署引用保留。本次不修改知识 Wiki，不把 hcom 选定当作安装或运行成功。

2026-10-18 后续实测 no_reusable_delta：复用“按当前任务选择验收依据”，按真实原生事件、原会话和产物分别验收。具体版本与单次能力边界写回本项目，不把结果推广为跨全部 CLI 的通用唤醒，也不新增共享知识页。

2026-10-18 no_reusable_delta：用户在 CM 中确认的具体取舍已写入现有项目决策；SpecMesh §8 已要求以减少用户协调与维护负担判断是否继续扩展。采用 Wiki/自动化开发范式与智能体协作.md 的“按当前任务选择验收依据”，本次只验证文档和停止状态，不为记录决定重新派发模型或验证线上服务。

already_covered：采用 Obsidian Wiki/自动化开发范式与智能体协作.md 的“远端任务恢复：先确认提交边界”，保留未知提交结果并先对账，避免重复触发。CapMesh 的复用原则也已覆盖本次选择。社区竞态补丁与具体命令保留在本项目，无需重复创建共享知识页。

2026-10-12 already_covered：按 Wiki/开发知识入口.md 的“换 Agent／中断恢复”和“Agent 完成／实际交付”路由，核对 Wiki/自动化开发范式与智能体协作.md 的“按当前任务选择验收依据”及 SpecMesh SPEC.md §8、CapMesh D021。共享原则已有准确覆盖；提示版本兼容与 worker 传递边界只影响本项目，写回现有 AGENTS、PROJECT、回调说明与决策，无新增共享知识页。
