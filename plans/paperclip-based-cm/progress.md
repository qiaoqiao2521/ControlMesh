# Progress

## Current
2026-10-20：本页保留已有 Paperclip 部署与运行所有权。CM 新方向为单 Harness 内的多 Agent、多模型／多 Runtime 协作，加入 MACPIE 模型统筹职责；具体项目与接入待确认。以后不研究跨 Harness，hcom 接入移出后续计划。见[项目方向](../../PROJECT.md)和[当前进度](../codex-callback-bridge/progress.md)。MCode → AGY 单次 idle 验收作为历史保留；本次不操作本页所列服务。

2026-10-14：最新运行恢复见[飞书本轮进度](../feishu-native-conversation-20261006/progress.md)。本机和六机插件已统一compat.9，436在途工作自然结束后接续；七处统一纯代码check/sync。BF同型缺监听已修复，本机worker-only重启恢复通过，本机/BF/436/Green/Moon/Cy新回复通过。Qia独立CM未配置，原Codex App桥保留。当前服务器事实仍回源Ops，不把版本统一当作全部业务闭环。

以下10月13日及更早内容保留历史验收范围。

2026-10-13：当前采用 Paperclip 原生生命周期与 CM 薄适配。最新入口按路径分别验收：

- [持续飞书私聊](../feishu-native-conversation-20261006/progress.md)：原插件统一 compat.8，436/BF/Green 已有连续私聊验收；2026-10-13 的[现场记录](../feishu-native-conversation-20261006/evidence/fleet-live-20261012.md)补充 Moon 凭据修复并恢复监听，Cy 新应用凭据与订阅已接入。Moon 入站对话、Cy route/nativeConversation 绑定及真实回复、qiaobird 独立 CM 接入仍待完成。问题卡/UI continuation 保留原边界，本次未复测现场。
- [Codex 原会话回传](../codex-callback-bridge/progress.md)：2026-10-11 QIA-100 的原生派发、完成事件、queue、原会话接续和文件核验通过；研究业务接受与回传回执分别记录。
- [运行归属与治理](../../PROJECT.md)：2026-10-08 的已记录范围为六台 VPS；当前运行事实回源 Ops，不将历史八机与 63 个 schedule 当作实时数量。
- [本次遗漏修复](../mesh-omissions-20261012/progress.md)：恢复 CapMesh 常用 main 入口，补齐当前状态引用与待返工接续；不恢复已取消的 Orca 或联合发行任务。
- [有界会审](../decision-consultation-v1/progress.md)：新会审增加来源/假设核对与反证/失败条件两个视角，旧回执兼容检查通过；本轮未运行真实咨询，模型效果待观察。

## Historical acceptance — 2026-10-01
2026-10-01：CM 使用 Paperclip 底座与薄适配，不修改上游核心。[全服务器迭代](../fleet-paperclip-agy-20261001/progress.md)已接受：8 台默认 cm/controlmesh 绑定各机独立 context/company，63 项有效 CM 定时任务转为 native active schedule；新服务持久启动，旧消费者停止。8 台 AGY 1.2.14 程序更新接受，各机不同账号，用户选择登录后置。

436 的默认 cm/controlmesh 与飞书消费者已迁移，旧 Python CM 停止并禁用，公众号 timer 保留。用户确认公众号协作用于日常产出、网站入口有进展；内容 QA、真实消息与运行时分别验收。436 post 消息复测状态见[对应进度](../436-paperclip-feishu/progress.md)。

bf2025 原有只读 cron CMB-7 经原 Claude/sonnet 真执行后 done/succeeded/exit0；另六台各一次无模型指标任务由根直接回读本轮产物与原生回执。BF14、greenrise12、colocrossing16、Moonrise21 的原时刻/时区和静默/业务策略保留；原停用任务、OS cron/timer、身份/config 不丢失。薄适配 107 项测试及 12 项参数化子测试通过，代码已推送。

全机只用飞书，Telegram 可停但身份/config 保留。bf2025、436 有各自既有飞书身份，其余 6 台缺自己的绑定。正常运维静默，业务产物和待投递状态保留；执行前方向核对仍为[已记录待选用需求](task_plan.md)，不自动新增模块。

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
Qia独立CM和普通用户AGY AUTH分别接续。Cy旧legacy运行已成功但未送达，保留核对、不重派。当前63项已退役、trigger为空，历史接管不作为实时调度状态。当前CLI入口不重复部署，业务和问题卡的独立验收边界保持。

执行前方向核对保持“待选用”，范围、采用/停止条件见 task_plan；不自动进入实施队列。

## Issues
已接受的本机文本链与服务器 CLI/调度接管不代表附件、完整群聊策略、各机飞书投递或全部业务发布通过。greenrise 历史 canary 阻碍不再用于否认本轮已完成的 headless 接管。

436 当前由根 Codex 整合接管，状态回源到其 task_plan/progress。既有 Orca 与 cron 遗留继续按 repository-closeout-policy/progress.md 交接给根 Codex。

## Next
登录和缺失飞书绑定按用户安排接续；436 有新消息时补待验收项，无新消息不持续盯守。根串行交付状态，并用既有收尾 CLI 将 Current 同步 CapMesh；不新增 Actions/cron/常驻 Agent，不重复已接受的模型或文本试验。
