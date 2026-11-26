# Decisions

只保留当前仍影响使用的决定。完整旧记录见 [清理前 DECISIONS.md](https://github.com/qiaoqiao2521/ControlMesh/blob/851d78b8989d07281d0082a5105f878a99f589c8/docs/DECISIONS.md)；历史待办不自动恢复为当前计划。

## 2026-11-26 — 记忆直接归 TraceMesh，并作为可选插件交付

用户纠正此前的“TraceMesh 提纯、CM 对接”方向：记忆直接迁移到 TraceMesh，CM 以后不负责。

把现有 DSH Companion Memory 的源码、测试、许可及研发记录迁至 [AgentTraceMesh](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md)，从 CM 删除插件目录和专属 CI。插件沿用已有 DSH 数据目录、companion 身份和记录格式，保留显式选择性旧文件导入；仓库迁移不会操作用户运行数据。

此前尚未推送的 `cm context`、`cm run --context` 和执行报告携带记忆回执方案已撤回。CM 维持显式执行与验收，宿主直接使用 TraceMesh 的独立能力。源码、数据兼容和部署分别记录；本轮不表示已更换用户机器上的插件安装。

## 2026-11-24 — 退役旧平台，交付一次执行与验收

用户确认现有方案仍未形成日常可用入口，允许删除旧 Paperclip 路线，并授权按本轮方案修改与推送。

决定：默认入口改为 `cm run`。组合一次显式命令、现有检查、产物核对和接续报告，让当前宿主根据真实结果继续修复或交付。无检查保留未验收状态，完成通知和 worker 自报成功不替代实际结果。

删除：旧 Python / TS Runtime、Paperclip / Orca 专有接线、旧面板及对应部署、发布和迁移入口。它们通过 Git 基线 `851d78b` 保留来源，不复制到新的 archive 目录。

当时保留：独立 SpecMesh 的 prepare/check、跨仓 closeout、agent-link 的已确认选择规则、可选 codex_callback 及其来源许可、独立 DSH 陪伴记忆；记忆归属已由 2026-11-26 决定更新。源码删除不停止服务器、不改生产配置、不删除私有数据；现有部署状态本轮不作推断。

接续：报告给出建议而非批准或强制停止。当前宿主可依据已有授权自主处理失败；脚本不再调模型、不自动重试、不创建后台任务库。普通小任务无需额外工作流文件或机器交接包。

研究借鉴限定为工程取舍：按任务决定是否协作、限制材料读取范围、保留可核验产物和来源。参考 [Kim 等，Nature Machine Intelligence 2026](https://www.nature.com/articles/s42256-026-01268-y) 与 [ScaleMAS 2026 预印本](https://arxiv.org/abs/2610.16120)。本轮没有复现这些论文，也不承诺论文中的收益；任务判断与报告由具体实现和实际验收负责。

验收：[本轮计划](../plans/cm-usable-orchestration-20261124/task_plan.md) 与 [进度](../plans/cm-usable-orchestration-20261124/progress.md)。以后只为真实任务复现的缺口补能力，不按厂商数量或框架功能表扩张。

## 2026-11-22 — 把开发工作流作为 CM 核心

保留的原则：需求、选定依据、修改范围、真实验收与接续由现有项目记录表达。SpecMesh 管当前事实，TraceMesh 提供历史证据，CapMesh 记录能力取舍，各宿主管工具、权限与原生会话。

首次实现的 `cm-workflow prepare/check` 只组合独立 SpecMesh 原生接口；材料新鲜度不等于业务通过。2026-11-24 增加实际执行入口，取代旧平台仍需留在工作树的约定。原始验收见 [历史进度](../plans/workflow-small-change-20261122/progress.md)。

## 2026-11-13 — AGY 退出自动派发

AGY 仅在用户显式点名时人工前台使用，不自动探测、不 spawn、不作为后台或降级候选。默认外部候选仅 Qoder；CBC 仅显式指定，ZCode 沿用 edit 配置，DSH 派发暂停。脚本兼容参数的存在不构成启用授权。

## 2026-10-25 — 围绕现有 CLI 做轻量适配

保留的调用边界：优先宿主原生子 Agent，必要时使用 agent-link 调用边界清楚的子任务；登录、模型、网络与原生会话由各 CLI 维护。短同步返回和后台接续分别验收。详见 [agent-link](agent-link-subagents.md)。

acpx / 统一 ACP、hcom 平台化接入和 Magpie 的 Codex 模型统筹不恢复为默认方向。一个工具能执行不代表有额度、会话可恢复或通知可送达。

## 2026-10-23 — 陪伴记忆保持独立可选

[DSH Companion Memory](https://github.com/qiaoqiao2521/AgentTraceMesh/tree/main/plugins/dsh-companion-memory) 保存个人陪伴材料，默认不向后台子 Agent 提供私人记忆。保留选择性导入旧文件的能力，不恢复 CM 通用记忆服务。代码测试与真实模型长期记忆质量分别验收。2026-11-26 起由 TraceMesh 独立维护。
