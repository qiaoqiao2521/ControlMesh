# Agent 调度与原会话接续

## Goal

2026-10-20 最新选择：CM 只推进单 Harness 内的多 Agent、多模型／多 Runtime 协作，加入 MACPIE 模型统筹职责，停止跨 Harness 编排研究和多厂商 Agent Runtime 平台建设。当前任务只记录决定、同步 CM／CapMesh／长期记忆并验证交付。MACPIE 具体项目待确认；不安装、不改模型或代理配置、不派发任务、不迁移服务。

2026-10-18 的 MCode + hcom 选择保留为历史；hcom 跨 Harness 接入已移出后续计划。MCode 原生后台完成通知仍可复用，已完成的 MCode → AGY idle 验收不重跑。Codex App 接收端继续保留原有 native queue；已有 Paperclip 服务保持原所有权。

2026-10-18 历史范围：发起方也可以是 AGY、MCode。用户批准一次 MCode → AGY → 原 MCode 会话的原生后台任务实测，已完成单次 idle 接续与独立验收。沿用现有登录，不安装 ACP、hcom 或新调度层；具体事实与未测范围见 progress.md。

先前停止决定继续有效：用户放弃 acpx／统一 ACP 试验，不恢复独立 ACP 登录或 App 切换。Codex 接收端继续复用完成通知、原会话 queue 和回执；下面保留已有 Paperclip 专用路径的实现与验收历史。

用户选择 codex_callback 的外部完成通知、原会话 native queue 与接续回执查询。复用社区 runtime，CM/Paperclip 继续拥有派发和任务生命周期。

用户最新范围：只在本机接入，不操作 436 或其他远端。

## Scope

- 固定社区 commit 5193e2ece5caf2ac1805800575e5567a972f657c，保留 MIT 与来源。
- 仅修复桌面先消费后 queue/start not-found 的回执对账竞态。
- 新增本机薄 CLI：绑定原线程/同服务/CM 原任务，接收已验证完成事件与交接文件，对外部 run 去重，查询 queue/turn 收据。
- 提供独立 cm-codex-callback 本机入口；保留现有 cm 与 436 模板，不重建调度器或任务生命周期。
- 保留历史 acceptance reference 与两次 idle/busy 记录，不重做原测试。后续用户授权即时试用：仅为 QIA-99 已结束 run 补发一次结果，不重跑任务、不重启 App、不修改生产 CM。
- 用户随后要求立即派发一个本地模型部署任务。新增 QIA-100 单轮研究，接原生完成状态事件到已验证 notify；只操作本机，不安装模型，不重跑 QIA-99 或 Night Lab 历史待审题。

## Plan

2026-10-20 记录阶段已完成：新决定与取代关系、已有入口、CapMesh 和长期记忆均已更新；新增链接／锚点与 diff 检查通过。提交后用既有 closeout 同步受管引用。历史遗留仍按 progress.md 的 owner／验收入口保留，不能混入本次文档提交。

1. 完成：核对社区实现、CM 入口、同服务原线程连接及 Git 遗留边界。
2. 完成：引入固定社区 runtime，做最小竞态修补和回归测试。
3. 完成：实现薄 CLI、完成事件去重与回执查询，补行为测试。
4. 完成：审查创建结果未知的恢复边界，完成必要检查、使用说明与本机入口安装。
5. 完成：本次已验证成果提交 c42900e 已推送 qiaoqiao2521/ControlMesh，远端 main 读回匹配；未接受遗留保留。
6. 完成：QIA-99 真实结果补发验收通过。忙时入队、同原线程唯一匹配持久 turn、交接文件及六份证据哈希读回一致；持续钩子与研究业务验收仍独立。
7. 完成：QIA-100 原生派发、完成事件自动投递 queue、同原会话唯一持久 turn 与文件读回均验通。独立审查判草稿需修订，issue 保持 in_review；暂停本次一次性 Agent 并读回。本次仅接受回传闭环，不接受草稿为部署成果。
8. 完成：最新复用与流程成本准则接到 CM 项目入口和新 callback；旧提示版本与原回执保留。38 项 Python、32 项 Node 隔离测试通过，通用默认提示与显式任务说明均已验证；未派发任务或操作远端。

## Next Step

本轮方向记录完成，按既有 Git／closeout 流程交付后收口。MACPIE 身份待确认；之后的多 Agent 任务限于同一 Harness，不补跨 Harness 测试或 hcom 接入。

## Acceptance

独立测试证明绑定只能指向同 daemon 已 loaded 的原 UUID；重复外部 run 不能生成第二个 callback；创建结果未知时保留事实且不自动重发；queue/start 消费竞态用同 client ID 历史回执核验。started 仅表示接续启动，业务目标完成需原 Codex 读取交接文件并独立验收。

本机完成钩子的具体任务按实际派发接入。跨主机事件/文件传输不属于当前范围；下次普通 App 启动的持久连接仍需独立验收。
