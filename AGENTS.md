# Project Instructions

## T3 Code 为主体

默认应用是锁定版本的原生 T3 Server/Web。先读 `PROJECT.md`，再按问题选读任务记录与源码。默认入口不能退回旧 CM Runtime，不另建第二套任务、会话、provider 或记忆平台。

当前主计划：`plans/t3-primary-20261126/`。简单任务无需新计划目录。`docs/README.md` 只是索引，不是必读清单。

## 实施与接续

- 动手前检查 Git 状态，保留其他 Agent 和并行对话的修改；交付前重新核对远端 main。
- T3 拥有执行、权限、会话与工作区。按需使用原生子 Agent，主 Agent 回读真实产物并负责最终交付。
- 已授权可继续的部分直接处理；具体错误驱动修复或换方法，不机械重试收费命令，不因 `next_action` 新增审批。
- `run.completed` 只是回合结束；检查点、业务验收、push、部署和视觉证据分别核对。
- 用户最终只维护 main；临时 worktree 用于并行隔离，完成后核对整合与清理。

## 入口与验证

- `npm ci --ignore-scripts` 安装锁定的官方启动器；`npm start` 真正启动 T3。
- 无参数 `cm` 会启动 T3，查看说明用 `cm --help`。`cm t3 ...` 不改写上游 argv、JSON 或退出状态。
- `cm verify` 只核验已有结果，不再次启动 Agent。显式检查与产物清单不是额外沙箱，命令沿用调用方授权。
- `cm run`、`cm-workflow`、`cm-closeout` 保留兼容用途，不强制普通任务生成交接包或跨仓同步。
- `npm run check:t3` 检查真实服务与 Web，未发起模型回合；不得把这表述成已审计上游全部 provider 探测。Python 使用现有测试、Ruff 和安装包 smoke，验证范围与剩余风险相称。
- `t3.json` 的 scripts 需要导入；`runOnSettle` 不是通用回合结束钩子，不能虚构自动接入或 T3 API。

## 上下文与执行器边界

记忆能力直接归 [AgentTraceMesh 独立插件](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md)：历史压缩、提纯、检索、存储与宿主注入均由它维护。CM 不维护记忆接入、上下文注入或记忆回执转发，不恢复 `cm context`、`cm run --context` 或另建记忆适配层。SpecMesh 保存当前项目意图与约束，T3 保存运行状态。历史线索仍须核对当前证据后再使用。

AGY 只在用户明确点名时人工前台使用，不自动探测、spawn 或降级派发；CBC 仅显式指定，ZCode 沿用既有 edit 配置，DSH 派发暂停。外部 Qoder 在具体任务需要时按现有规则选用，不因换底座启用旧候选。已退役组件从 `docs/retired-components.md` 的固定历史追溯。

## 交付

优先复用上游，不复制完整 T3 多平台源码。升级时同时核对 npm 锁、`t3-upstream.json` 和实际接口，运行真实 smoke。当前源码、模型连通、飞书通知和生产部署分别报告，不把合成测试称为模型验收。

不提交凭据、`.env`、原生会话、个人记忆、运行报告、日志、依赖或构建输出。按已有授权提交并推送 main；源码退役不操作服务器或私人数据。项目方向、模块职责和关键决定分别更新 PROJECT、ARCHITECTURE、DECISIONS，本轮事实写原任务记录。
