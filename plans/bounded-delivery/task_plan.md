# ControlMesh：分批完成 TS 迁移，再验收协作与原生续接

> 2026-09-22：本文件为历史方向与证据，完整 TS 不再是默认投入目标。
> 当前入口是 [CM × Orca bridge v0](../cm-orca-headless-bridge-v0/task_plan.md)。
> 下文日期、状态与 Next Step 是旧快照，不授予恢复旧 worker、提交或切换权限。

日期：2026-09-14。状态：queued，计划已准备，未启动实现。本计划接替 runtime-convergence 的混合执行方式；旧代码、验收 ID 和证据保留。Ops 不在本轮范围，不自动恢复 Goal。

## 目标与唯一入口

CM 负责稳定任务身份、执行/取消/恢复、provider 预检、持久化、消息投递及设备协调。完整 TS 是终点：约定生产核心在没有旧 controlmesh Python 包的干净环境运行；Python 可以作为隔离 reference，不能藏在 TS 后面承担生产控制链。

按优先级先交付独立 SpecMesh，再交付独立 History，CM 当前排队。用户另行选定一张 CM 卡时，可直接执行该卡已有授权范围，不需要逐命令询问。单次结束必须交付并退出，不继续领取下一张卡。

从 [PROJECT](../../PROJECT.md) → 本计划 → 本次选定卡涉及的代码/证据渐进阅读。当前快照、已复用成果和失败见 [findings](findings.md)，派发/验收状态见 [progress](progress.md)。

## 范围与项目边界

- 迁移维持既有行为，新增多设备/协作能力另设轨道，不能为修一个 parity 问题同时重做协议、界面和整个调度器。
- SpecMesh 是独立规范/机器能力，History 是独立历史证据服务；CM 消费版本化接口，二者的独立发行不等待 CM 默认切换。
- 外部官方 CLI 自身的实现语言不属于 CM 重写范围；可选 SpecMesh Python 工具也不是旧 CM 核心。但不得把自有控制逻辑重新包装成所谓外部 Python 工具规避 TS 验收。
- Claude、Codex、OpenCode、CBC、AGY 及已有受支持 transport 都必须在支持矩阵中有明确归属；AGY 不等同旧 Gemini。新增 profile 与既有路径迁移分别记录，不靠删掉支持范围完成迁移。
- 正常本机主工作区继续使用。已有直接 push 授权有效；不要强制制造 PR/worktree。仅真正并行、目录不独占时另用隔离分支/worktree，显式纳入原目录的相关未提交成果。
- 本轮不做 Ops、生产 cron 调整、浏览器/微信/账号操作、fleet 部署和新的模型轮询/自动化。未来真实 provider 或本机切换卡须写清已授权的具体范围，不能把本规划当任意账号操作授权。
- 不恢复取消任务 77f04609、7738c5eb；旧 Goal 保持暂停，不利用上下文压缩/换 session 绕过停止限制。

## 可复用基线：不要重写已存在能力

核对基线为 main / 3596526525c2b74f1e20b09983d8048cb384baad；该 HEAD 的 tracked worktree 在规划开始时干净，四个 delegation untracked 文件保留。当前稳定版及本机 CLI 0.43.0 仍是 Python。既有 TS kernel、state/queue、provider/container、cron、mailbox/device、History/SpecMesh candidate 都是后续收敛起点，不从空目录重新移植。

旧计划 [CM-R0～R7](../runtime-convergence/task_plan.md) 和 [CM-A01～A10](../runtime-convergence/task_plan.md#acceptance-matrix) 继续作需求与证据索引。旧日志的 passed 只对其 SHA/profile/场景成立，不能代表下面整项通过。

## 三条轨道与固定验收分母

每个轨道只计算“出口全部通过”的原有阶段，partial/unknown 不给半分；一项被反例推翻就重开。当前 0 不代表没有实现，而是尚未完成整体出口。不合成三项目的总百分比，不继续使用含 Ops 的旧 7.4%。

### T：完整 TS 迁移，0 / 5

| ID | 可交付行为与出口 | 当前状态／证据 | 主要实现入口 |
|---|---|---|---|
| CM-R0 | 一张可复现的行为/所有权台账：每个存储、关键字段、副作用、入口、迁移/回滚 owner 对得上 reference 和 TS；支持范围冻结。 | partial；现有哈希/字段 inventory 不是完整台账。 | scripts/generate_runtime_ownership.py；plans/runtime-convergence/python-ownership.json；controlmesh/tasks、runtime、cron；packages/controlmesh-runtime-core |
| CM-R1 | 状态机、事件、队列、取消、deadline、进程监督和终端工作台正常可用；隔离 Python/TS 对照覆盖成功/失败/超时/取消/崩溃恢复，shadow 不产生第二次真实副作用。 | partial；来源事件不符合项与完整 process/UI 出口开放。 | src/kernel.ts、local-task-runtime.ts、local-runtime-config.ts；scripts/cm-runtime.ts；旧 terminal-product-v1 计划 |
| CM-R2 | 所有迁移存储及任务目录/工件/native references 可 dry-run、验证摘要、中断恢复和回滚；唯一 writer 交接。 | partial；registry 导出不能代表多存储生产恢复。 | src/database.ts、cron-store.ts、host-job-store.ts；scripts/legacy-export.ts；旧 rollback-rehearsal.md |
| CM-R3 | 受支持 provider、tool/source/workspace、quota/auth/model、transport 全路径由 TS 控制；真实 profile 验收、原生权限、进程树清理和投递对账有证据。 | partial；CBC/AGY Python hostjob bridge 不是独立 TS adapter；Codex synthetic 服务端不是真实账号。 | src/providers、local-runtime-config.ts；controlmesh/providers、messenger；旧 delegation/README.md |
| CM-R7 | 干净安装无需旧 Python 核心；既有支持流程、完整工件/协议、升级/回滚及 terminal 通过；按限定本机 canary 切换默认入口，先撤旧 writer 再启新 writer；发布 SHA/安装/运行一致。 | planned；当前 cm 仍为 Python，未进行默认切换。 | pyproject.toml；package.json；scripts/cm-runtime.ts；packaging/CI 与现有入口 |

表中 src、scripts 在 TS 部分均指 packages/controlmesh-runtime-core/ 下的路径；开始卡前用当前仓库核实，不能按文档路径猜不存在的接口。

### D：多设备与协作，0 / 2

| ID | 可交付行为与出口 | 当前状态 |
|---|---|---|
| CM-R4 | 两个受控设备的身份/能力/工作区/lease/fence 可核对；过期、时钟偏差、分区、重启后旧 worker 无法写回或重投。 | partial；已有 ARM64/x64 实际结果复用，完整 profile/故障矩阵仍缺。 |
| CM-R5 | 父子任务与并行 Agent 可持久收发、引用证据、交付一次待验收事件；重复/乱序/重放、有限 fanout/队列、backpressure、取消传播及重启收敛。 | partial；有 native MCP/mailbox 与局部并行设备证据，完整 topology 尚未关闭。 |

D 当前 queued。不是重写一次现有 device/mailbox；待 T 的相关 owner 可用后逐一复用并补矩阵。只做两个受控节点，不顺带执行 Ops fleet。

### N：真实 Agent 续接，0 / 1

| ID | 可交付行为与出口 | 当前状态 |
|---|---|---|
| CM-R6 | 通过 History 可选候选选择已有 session，校验 provider/store/device/repo/revision/current scope，原生续接并读取当前文件，产出被任务 owner 接受的实际结果；拒绝 stale/missing/wrong scope，验证取消与恢复，SpecMesh required gate 不把 unknown 升为 pass。 | partial；真实 OpenCode/Claude 局部续接已存在，完整 provider/profile/外部 closeout 仍开放。 |

N 当前 queued；相同 CM task ID、原生相同 session、全新 session 加结构化交接是三种不同事实。跨 provider 只能明确标记新的上下文交接，不能承诺原生内部记忆无损迁移。已知验证过的同 session 场景不重做实现。

## 分批方法：采用现有 pnpm + Bun + TypeScript 工具链

先固定 reference → 选择一个真实行为域 → 定义可观察输入/输出及副作用 → 复用/补齐 TS → 同输入隔离对照 → 新上下文审查 → 至多两轮修正 → 一次集成验收 → 记录并退出。

行为对照包括返回值、错误类型/退出码、状态事件与来源、数据库/文件效果、取消和重启恢复；不只比较 JSON。reference 与 candidate 使用各自临时状态，绝不同时对生产库或真实账号执行 A/B。已确认的旧 bug 用显式“预期行为修正”卡处理，不为保持 bug 而移植，也不暗改 golden。

移植规则随一个行为域补到已有台账：Python 异常→明确错误结果，进程/thread 生命周期→受控 child/abort/deadline，文件/DB 更新→事务和版本检查；每条都要有对应 observable fixture。不要先生成全仓翻译指南再迟迟不交付。

共享 schema、package/lockfile、生产入口和集成由一个 owner 写；实现者只动该卡白名单。跨仓协议确需改变时保留可审查提案，另立适配卡，不随手修改另外两个仓库。

## 唯一已细化、尚未选定的 CM 卡：CM-R0.B1

**名称：修复当前 standalone SpecMesh topology publication CI 的确定性与诊断。**
**状态：queued；当前全局下一张实现卡属于 SpecMesh，此卡未启动。**

用户可观察结果：要求文件未变化时，有证据说明 publication completed；变化时明确 blocked。测试超时须正确清理且不能留下污染后续用例的工作。不是单纯把 CI 染绿。

基线与复用：

- 起点 3596526；执行前重读 HEAD/diff/本卡。若已有他人修复，先验收该改动，不重复实现。
- 当前失败证据是 CI 34764077070 / job 103741822771：device-topology-artifacts.test.ts 的 changed=false 超 5000 ms，其后 completed/blocked 不符；尚未证明原因。
- 复用现有 fixture、scheduler、SpecMeshPort 与 pinned 独立源码，不重建测试 harness。
- Python reference 固定同一基线，其余 profile 原样保留；这张卡不运行收费模型。

允许范围：packages/controlmesh-runtime-core/test/device-topology-artifacts.test.ts 和该 fixture 确实需要的 helper；必要时该测试直接涉及的 adapter/scheduler 最小修复；本计划 progress/findings。共享协议、锁文件、CI 门槛全局配置、其他仓库和生产状态不在本卡范围。若根因必须越界，报告原因和最小后续卡后退出。

执行与验收：

1. 保存运行版本、环境、SpecMesh 源 SHA、计时分段与原错误。用一次单文件命令有限复现；没复现不能说问题消失。
2. 分清 test timeout、子进程 deadline、cleanup 导致 blocked 和真实 gate 拒绝。给至少一个能区分假设的检查，不无脑多次跑全套。
3. 修正真实原因；若确属合理耗时超过测试预算，必须有计时证据、有限 deadline 和取消清理断言后才调整该用例预算。不得删除 completed/blocked 断言。
4. 原 changed=false/true 两条出口都通过，失败/超时后无遗留 owned process 或后台 publication；再运行受影响的 SpecMeshPort/topology 检查及 typecheck。
5. 一个新上下文 reviewer 检查 diff、原反例、通过证据与权限/副作用边界；最多两轮修正。若本批包含获授权提交，必需 CI 必须对应最终 SHA，旧 CI 不能代替。
6. 输出结论、diff/日志位置和唯一建议下一卡后退出。通过本卡不将 CM-R0 或 SM-P2 整阶段标完成。

已存在的命令入口（在仓库根，先确认依赖已安装；不要为执行它而隐式升级工具链）：

- pnpm --filter @controlmesh/runtime-core typecheck
- bun test packages/controlmesh-runtime-core/test/device-topology-artifacts.test.ts
- bun test packages/controlmesh-runtime-core/test/specmesh-port.test.ts

源码与测试依赖使用现有 CI 的 CM_SPECMESH_TEST_ROOT 环境变量，指向核实过的独立 SpecMesh 源码（当前 CI pin 为 d393c548a2a58989d65e6cdbd60a36e9a81a444f）；不得拿不存在的默认路径运行后把 skip 当成功。源码可保留其文档 dirty，但产品源/契约变化须记录并重新核对。此处命令是后续验收说明，本次规划没有运行。

## 后续卡队列：只列边界，不预写几十张实现细节

| 卡 | 一次只交付的能力 | 所属出口 |
|---|---|---|
| CM-R1.B1 | 修正 schedule/agent/recovery 的执行事件来源；明确 actor 与 task origin 的不同字段/语义，针对本次真实反例验证。 | CM-R1、CM-A05 |
| CM-R0.B2 | 在已有 TaskHub lifecycle 域做一个完整 owner/field/effect/reference→TS 对照样本；验证方法可复用后再扩其他域。 | CM-R0 |
| CM-R2.B1 | 选择一个尚未闭合的迁移存储，做目录/工件 lineage 与中断/回滚证据，不并行改所有 store。 | CM-R2 |
| CM-R3.B1 | 从已核实的支持矩阵选一个缺口 profile，闭合 preflight→执行→取消/恢复→结果对账；CBC/AGY 单独 profile，不静默切更贵模型。 | CM-R3 |
| CM-R7.B1 | 所有迁移出口通过后才细化一次本机安装/升级/单 writer 切换卡。 | CM-R7 |
| CM-R4.B1 / CM-R5.B1 / CM-R6.B1 | 按各自轨道选一个未通过场景，复用真实既有证据；每个 ID 单独派发，不能合成一个长程 Goal。 | D/N 轨道 |

## 验收、费用和停止协议

- 默认一个实现者加一个按需新上下文审查者；仅独立目录/接口/状态时增加第二实现者，最多三个活跃模型上下文。不递归生成更多代理。
- 实现/简单测试优先使用用户配置的 CBC/AGY；当前可用性必须通过已存在的非推理配置/状态检查与实际失败记录判断，历史使用记录不是额度证明。只因 unavailable 不可自动换收费更高模型。
- 每卡一次实现、一次独立审查、最多两轮修正；首个真实账号 probe 失败后遵守 typed quota/auth/reset，不连续试探。工具支持硬限额就使用；不支持则明确无硬保证，逐次有限调用。
- 成本/token 读不到写 unknown；记录实际调用次数和修正轮数。运行进程退出 0、部分 JSON SUCCESS、报告写了 PASS 都不能替代应用任务验收。
- 发生额度/鉴权失败、需要越界、两轮无实质进展、独占写入无法确认或外部结果 unknown，就保留成果并给出具体阻塞后退出；不能靠换 session 重置轮数。
- 普通可逆开发与既有授权不反复审批；任务卡本身不是发布/部署的自动命令。是否包含提交/发行/本机切换，在派发记录中明确；已有直接 push 授权无需另走强制 PR。
- 每批结果记录：ID、可用行为、实现/验收/发行/安装/运行分离状态、准确 HEAD 与 dirty 指纹、命令和证据、real/synthetic 边界、费用或 unknown、调用/修正次数、剩余项、下一张建议卡。审查者根据原出口裁决，不能由实现者自签完成。

## 回滚与失败保护

新卡不得 reset/clean 其他工作，不能复制 provider 私有 DB 作为设备协议。未知外部效果先对账再重试。正式切换前保存 version/digest，演练多存储恢复并保持取消状态；先 fence 旧 writer，再启 TS。发布后发现副作用重复或授权扩大，停止相关入口并保留证据，不能靠重放任务“自动回滚”。

## Next Step

本轮交付这份独立计划并退出。CM 继续 queued；用户选定 CM-R0.B1（或明确的其他单卡）后，仅执行该卡。优先完成 SpecMesh 的独立交付，不自动开始下一批。
