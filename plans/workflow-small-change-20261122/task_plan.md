# CM 首条工作流：带证据的小改动交付

> 历史记录：以下保留原任务日期与验收范围，不是当前待办或机器状态。文中的历史文件链接固定到清理前提交；当前方向见 [PROJECT.md](../../PROJECT.md)，当前验收见 [本轮进度](../cm-usable-orchestration-20261124/progress.md)。

## Goal

把用户确认的开发工作流落为多个 Harness 可读取的现有文件与最小命令入口，以一项真实文档修复验证交接和独立验收。

## Constraints

- 使用现有计划、SpecMesh 原生 handoff 与消费前核验；不增加索引、后台服务、状态库、执行器或模型适配。
- Harness 继续负责工具、权限、会话和执行；材料有效不等于业务验收或授权。
- 任务路径和修改范围由调用方独立给出，历史定位、来源修订与现有部署所有权保持不变。
- 用户已授权直接交付 main；只提交本轮改动，推送前检查远端基线。

## Requirements

- 提供可独立运行的 `python3 -S -m controlmesh.workflow prepare|check`，透传真实 SpecMesh 结果，拒绝旧接口、空输出和矛盾的成功标记。
- 在独立进程间消费材料，覆盖所选文件变化、HEAD 变化和重新生成材料；不将这些测试宣称为跨厂商实测。
- 当前入口、架构和决定统一为可复用工作流；既有 CLI 调用和运行服务保留原边界。
- callback 样例 R1：纠正旧 MACPIE 待接入导语；R2：后文身份、生命周期与去重规则保持原样；R3：链接与实际 diff 通过核验。

## Scope

`controlmesh/workflow.py`、`tests/workflow/`、`pyproject.toml` 的命令入口、现有 CI 的独立集成检查、项目入口文档、`docs/workflows/small-change.md`、本计划目录，以及 callback/agent-link 当前说明。

## Next

在下一项真实开发任务中复用本流程，按实际交接需要记录接续效果。
