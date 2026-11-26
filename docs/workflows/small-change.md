# T3 中的任务与可选交接

在 T3 原生线程中明确可观察的目标，按需读取项目材料，完成实施、独立验收和交付。任务计划保存业务目标与事实，T3 保存运行状态；正常接续不要求重新制作材料包。

## 完成一项改动

先读目标项目的 `AGENTS.md`、`PROJECT.md` 和有关代码，检查当前 Git 状态。用已有记录写清目标、修改范围、验收方法和停止条件；普通小任务不用另建编号系统。

历史有助判断时，按需通过 AgentTraceMesh 查到原始片段，再回读当前代码。SpecMesh 的 `code://`、`mem://`、`spec://` 或 `area:` 可提供关联；旧摘要不自动成为当前事实。

实施时使用 T3 中所选执行器的原生工具。可独立分工的任务才交给子 Agent，传入必要材料和同一验收标准。结果生成后，按需用 [`cm verify`](../verify.md) 执行已有检查并观察产物；主 Agent 仍需回读实际改动。外部独立命令才使用兼容 `cm run`。

在当前授权范围内交付，记录实际验证、未覆盖项和必要下一步。执行失败按事实继续修复，不能只把 `done`、完成通知或交接检查当作成功。

## 真正交接时核对材料

T3 的线程恢复与执行器交接沿用原生能力。只有接手者需要独立、可核对的项目材料时，才使用兼容 `cm-workflow` 组合 SpecMesh 导出与消费前核验；它不派发任务、不调用模型、不创建新的状态库。

从 CM checkout 根目录运行。将路径、任务和 `CURRENT_FULL_GIT_SHA` 换成真实值，任务和范围由当前已确认目标独立给出，不盲从收到的材料反推。

```sh
python3 -S -m controlmesh.workflow prepare \
  --repo /absolute/project \
  --task plans/your-task \
  --specmesh-root /absolute/specmesh \
  --expected-head CURRENT_FULL_GIT_SHA \
  --scope src/selected_file.py \
  > /absolute/private-output/handoff.json
```

接收者在消费前用同一任务和范围检查：

```sh
python3 -S -m controlmesh.workflow check \
  --repo /absolute/project \
  --task plans/your-task \
  --specmesh-root /absolute/specmesh \
  --scope src/selected_file.py \
  --handoff /absolute/private-output/handoff.json
```

`--scope` 可重复。材料保存在计划树外的私有目录，避免材料把自身纳入范围。已安装包时也可用 `cm-workflow` 替代上述模块命令。

`executable=true` 只说明材料通过当前消费前检查，不授予执行权限，不证明产物正确。工具缺失时普通可执行工作可以继续人工核对，同时注明机器交接未验证。

正常改文件、更新计划或提交后，旧包过期是预期行为；仍需交接时更新原记录，用当前 HEAD 重新生成，再检查。没有接手者时无需每一步制作材料包。

出现状态冲突或截断警告时回读原文件。上游机器提取不能理解所有中文否定式，材料也可能因数量限制而省略内容，不能为得到通过状态删除失败事实。

## 已有证据

2026-11-22 已在本地独立 SpecMesh checkout 验证材料导出、跨进程消费、失效拒绝和一次文档修正。该记录不等于不同厂商 CLI、跨机器或后台恢复验通。原始结果见 [进度](../../plans/workflow-small-change-20261122/progress.md)，当日 callback 样例见 [固定版本](https://github.com/qiaoqiao2521/ControlMesh/blob/851d78b8989d07281d0082a5105f878a99f589c8/docs/codex-callback.md)。
