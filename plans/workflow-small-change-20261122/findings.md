# Findings

> 历史记录：以下保留原任务日期与验收范围，不是当前待办或机器状态。文中的历史文件链接固定到清理前提交；当前方向见 [PROJECT.md](../../PROJECT.md)，当前验收见 [本轮进度](../cm-usable-orchestration-20261124/progress.md)。

## 2026-11-22：复用边界

- ControlMesh 起始 main 为 `31d65d540711f429fe583675ad090e40f562f4f3`，开始时工作树干净。
- SpecMesh 使用独立 checkout `1e19bdf8093b57326cbadfa7cd9026b033c000ba`；AgentTraceMesh 已合入的身份修复为 `b9e1e739f64de8ce6918a96c2eebb436064723bc`。
- 现有 `controlmesh/cli_commands/specmesh.py` 向 stdin 写 `prepare_handoff`，但未传 `--handoff json`，仍接收旧检查结果。不能据此声称已接入原生材料导出。
- 新入口只组合 SpecMesh `--handoff json` 和 `--verify-handoff`。SpecMesh 继续拥有 schema、来源绑定、指纹和内容验证；CM 不复制它的索引或安全实现。
- 既有 `controlmesh.closeout` 检查声明的提交与文档片段，不执行业务验收；旧 planning_files 与 TaskHub 不作为首条工作流的前置条件。
- callback 导语仍引用 2026-10-20 的 MACPIE 待接入方向，与后来的决定冲突。修正导语是本轮真实的小改动样例；其余桥接语义保持原样。
- 当前派发 Skill 与配额脚本默认仅 Qoder；AGENTS 和 agent-link 文档的旧 Qoder→AGY 默认链需要纠正。AGY 仅显式人工前台，普通工作流不触发额度探测。

## Evidence

基线与实现依据：`controlmesh/cli_commands/specmesh.py`、`controlmesh/closeout.py`、独立 SpecMesh 的 `specmesh_port/__main__.py` 与 `handoff.py`；本轮实际验证记录在 [progress.md](https://github.com/qiaoqiao2521/ControlMesh/blob/851d78b8989d07281d0082a5105f878a99f589c8/plans/workflow-small-change-20261122/progress.md)。

## 事实边界

流程提供可读约束与交接材料。业务验收由执行者回读真实产物、运行必要检查并记录；`executable` 只表示材料可消费。普通变更使旧材料失效时，应更新原计划并重新生成，不锁任务或改旧指纹。跨厂商执行、Windows、已有设备和服务状态均需各自实测。
