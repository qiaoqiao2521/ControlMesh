# Decisions

只保留当前影响使用的决定。历史方案与当时的验收见 [0.44.0 决策快照](https://github.com/qiaoqiao2521/ControlMesh/blob/59014053939707b98a9fea3510400fdf02d468f5/docs/DECISIONS.md)，历史待办不自动成为当前要求。

## 2026-11-26 — 以 T3 Code 为主体

用户明确要求以 T3 Code 为主体开始改造。默认产品采用未修改的上游 Server/Web，锁定 `t3@0.1.12` 与提交 `ca81b7b97a1c4b91e5ac25768d0f6629f37732fd`；`npm start`、无参数 `cm` 启动 T3。保持上游界面、会话、Git、持久状态和权限边界，不复制完整源码或再建 CM 控制台。

CM 的自定义范围收缩为透明接入与独立验收。`cm verify` 只核验已有结果，区分检查通过、当前源码证据和远端提交确认；退出 0、完成通知或 T3 回合结束均不能替代业务验收。主 Agent 沿用已有授权接续，报告不增加审批步骤。

`cm run`、`cm-workflow`、`cm-closeout` 保留为显式兼容工具，普通任务不强制经过它们。`t3.json` 动作需要导入，不作为每轮完成钩子；本轮没有新增无限重试或自动唤醒平台。

DSH 陪伴插件由 TraceMesh 独立维护，从 CM 源码和 CI 移出；删除 Codex 专有回调运行时、依赖旧回调的派发 Skill 和 DSH API 启动器。来源、许可与当时记录通过 [固定历史链接](retired-components.md) 保留，不新建归档副本，不删除个人数据，不操作旧服务器。

## 2026-11-26 — 记忆直接归 TraceMesh，并作为可选插件交付

用户纠正此前的“TraceMesh 提纯、CM 对接”方向：记忆直接迁移到 TraceMesh，CM 以后不负责。

现有 DSH Companion Memory 的源码、测试、许可及研发记录迁至 [AgentTraceMesh](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md)，从 CM 删除插件目录和专属 CI。插件沿用已有 DSH 数据目录、companion 身份和记录格式，保留显式选择性旧文件导入；仓库迁移不会操作用户运行数据。

此前尚未推送的 `cm context`、`cm run --context` 和执行报告携带记忆回执方案已撤回。记忆存储、召回、维护和宿主注入完全由 TraceMesh 负责，宿主直接使用其独立能力；CM 不设记忆代理、注入参数或回执转发。源码、数据兼容和部署分别记录，本轮不表示已更换用户机器上的插件安装。

## 2026-11-26 — 项目材料与历史证据各归其位

T3 保存原生运行状态；SpecMesh 保存项目意图、约束和职责；TraceMesh 独立负责记忆、历史压缩、提纯、缺口检索与交接证据。本轮不建立另一份 CM 记忆库，不复制整段会话，不强制每个任务同时启用全部 Mesh。

需要并行时采用 T3 或执行器原生分工。普通小修改使用原任务记录，真正交接时才导出所需材料；材料有效仍不等于任务完成。

## 延续的执行器选择约束

T3 使用已配置、确实可用的执行器。需要 T3 之外的 CLI 时，保留 [Qoder 等显式兼容路径](agent-link-subagents.md)，不恢复通用额度路由或定时探测。

AGY 仅在用户显式点名时人工前台使用，不自动探测、派发或作为降级候选。CBC 仅显式指定；ZCode 沿用 edit 配置；DSH 派发暂停。上游支持某执行器不代表本项目自动启用它。

## 验证与交付范围

云端源码与实际本地运行分别验证；真实模型登录、飞书往返、既有生产服务迁移分别报告。当前任务的 [计划](../plans/t3-primary-20261126/task_plan.md) 与 [进度](../plans/t3-primary-20261126/progress.md) 是本轮证据入口。
