# ControlMesh Project Context

## 当前方向（2026-11-26）

用户明确要求以 **T3 Code 为主体** 改造和精简。默认产品入口是固定发行版的原生 T3 Server/Web；CM 保留必要接入、独立验收和兼容工具。不得把 `cm run` 改名后继续充当第二套执行平台。

T3 拥有会话、provider、任务、工作区、Git、权限和恢复。记忆直接归 [AgentTraceMesh 独立插件](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md)，包括存储、压缩、提纯、召回和宿主注入；SpecMesh 保存经核对的项目意图、约束和索引。CM 不负责记忆接入、上下文调用或回执转发，不复制聊天、运行状态或记忆目录。

## 当前入口

| 入口 | 职责 |
| --- | --- |
| `npm start` / `npm run serve` | 真正运行未修改的上游 T3 应用 |
| `cm` / `cm t3 ...` | 透明启动固定 T3，不另建会话、调度或自动重试 |
| `cm verify` | 核验现有产物、已有检查、当前源码和可选远端交付 |
| TraceMesh 插件（独立仓库） | 由宿主按需直接使用，CM 不提供记忆代理入口 |
| `cm run` | 独立外部命令的兼容入口，不是默认产品流程 |
| `cm-workflow` / `cm-closeout` | 真实交接与显式引用同步，普通任务无需使用 |

固定上游版本和来源见 `t3-upstream.json`。云端环境、执行器登录与飞书接入，必须分别依据实际连接验收；源码改变不等于生产迁移完成。

## 取舍

- 保留原生多 Agent、远程访问、断线恢复、检查点和工作区隔离；最终交付到 main。
- 以当前授权持续推进，具体错误驱动修复或换方法，不增加重复审批。
- 回合结束、退出 0、历史成功、文件存在都不单独等于任务完成。
- 不重建模型代理、统一认证、额度路由、调度数据库、记忆平台或固定多角色流程。
- 不恢复 AGY 自动探测/派发、暂停的 DSH 执行通道或未选用的消息渠道；保留 Qoder 明确选用的外部能力边界。
- DSH 陪伴插件源码、测试和研发记录迁至 TraceMesh；专有 callback 与旧派发 Skill 从当前 CM 源码退役，私人数据不在此次清理范围。

## Current

实现与证据集中在 [本轮计划](plans/t3-primary-20261126/task_plan.md)、[发现](plans/t3-primary-20261126/findings.md) 与 [进度](plans/t3-primary-20261126/progress.md)。本轮已整合 main 的记忆归属迁移提交 `2c49512`；迁移范围与验收见 [TraceMesh 进度](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/plans/memory-plugin-migration-20261126/progress.md)。T3 主体改造沿用这一边界。
