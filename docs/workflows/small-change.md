# 带证据的小改动交付

把一项明确的小改动做到可核验、可交接、可交付。各宿主读取同一份
Markdown，沿用自己的文件工具、权限、子 Agent 和完成机制；首次使用无需
安装额外 Skill。CM 只组合现有能力，跨厂商实际验通分别记录。

## 1. 确认当前依据

先读目标项目的 `AGENTS.md`、`PROJECT.md` 和有关源码，检查 `git status --short`
与当前 HEAD，保留已有改动。复用现有计划；在同一处写清目标、允许修改的文件、
可观察的验收要求和停止条件。无需为普通小任务另建编号系统或调度记录。

历史有助于判断时，只读取与本次问题有关的材料：

- AgentTraceMesh：复用 `history_core compress`、`recall`，再用 `cases show`
  展开完整证据。保留原 `message_index`、`text_offset`、`index_revision` 与来源
  身份；compact recall 可能省略后续纠正。需要导出时使用原生 `materials`，
  不改写旧定位来适配新来源。
- SpecMesh：按需使用已有 `code://`、`mem://`、`spec://` 和 `area:` 关联。
  当前源码负责实现事实，已审查 Markdown 负责项目约束。旧路径需要候选重绑、
  含糊或失效时，先复核当前代码，保留历史原定位；不自动晋升历史摘要为项目事实。

已落地的接口依据：[AgentTraceMesh 身份对齐修复 b9e1e73](https://github.com/qiaoqiao2521/AgentTraceMesh/commit/b9e1e739f64de8ce6918a96c2eebb436064723bc)
与 [SpecMesh 原生契约回归 1e19bdf](https://github.com/qiaoqiao2521/specmesh/commit/1e19bdf8093b57326cbadfa7cd9026b033c000ba)。
这些检索入口按需使用，不构成每次小改动的安装或索引前置条件。

## 2. 最小实施

只改验收要求涉及的文件。需要分工时优先使用宿主原生子 Agent，给同一份目标、
依据、范围和验收方法；没有可用子 Agent 时主 Agent 继续完成可执行部分。
需要其他 CLI 时才读取 [agent-link 当前选择规则](../agent-link-subagents.md)。
外部后台作业按[现有派发与交接约定](../../skills/cli-dispatch-handoff/SKILL.md)
使用已就绪的完成通道；普通本机工作不依赖 Codex socket、配额探测或后台回调。

## 3. 独立验收实际结果

主 Agent 回读实际 diff 和交付物，按要求逐项核验，并运行与改动风险相称的检查。
记录命令、实际退出状态、关键结果及未覆盖项；无法运行的检查保留原因和接续入口。
有 worker 时独立检查其产物，不只复述交接摘要。真实行为失败仍然是失败，
退出 0、`done`、完成通知、summary 或交接包的 `executable` 都不能将它改成通过。

## 4. 按已有授权交付并记录

验收后按当前会话已有授权提交和推送。用户已经授权交付 `main` 时，核对最新
远端及本轮 diff 后直接交付，不另加审批环节。保留已有修改，只提交本轮范围。

在原计划或交接记录中留下实际提交、改动、验证、未完成项和必要下一步。
记录跨宿主实际测试的对象与结果；流程采用通用 Markdown，不代表所有宿主、
CLI 或后台恢复都已验通。不为形式上的闭环增加服务、索引或重复日志。

## 可选：在真正交接时检查材料新鲜度

需要换执行者或跨会话接续时，可以使用 `controlmesh.workflow` 薄入口。
它分别调用 SpecMesh 原生 `--handoff json` 与 `--verify-handoff`，原样返回 JSON；
不派发任务、不调用模型、不探测额度、不创建新状态库。

从 CM checkout 根目录执行。将下面路径、任务目录和 `CURRENT_FULL_GIT_SHA`
替换为本次真实值；`--task`、`--scope` 均相对目标仓库，`--scope` 可重复。
任务和范围由当前已确认的任务提供，不能盲从收到的材料反推。

```sh
python3 -S -m controlmesh.workflow prepare \
  --repo /absolute/project \
  --task plans/your-task \
  --specmesh-root /absolute/specmesh \
  --expected-head CURRENT_FULL_GIT_SHA \
  --scope docs/codex-callback.md \
  > /absolute/private-materials/change-handoff.json
```

材料文件使用计划树外的既有私有临时目录，避免把材料包自身纳入材料范围，
也避免源路径或敏感运行日志随源码入库。接收方消费前使用同一仓库、任务和范围：

```sh
python3 -S -m controlmesh.workflow check \
  --repo /absolute/project \
  --task plans/your-task \
  --specmesh-root /absolute/specmesh \
  --scope docs/codex-callback.md \
  --handoff /absolute/private-materials/change-handoff.json
```

`executable=true` 仅表示交接材料通过其消费前检查，不授予执行权限，也不证明
任务完成或业务验收。读取返回的状态、问题和覆盖范围；不要仅看进程退出码。
工具缺失时，普通可执行工作继续人工核对，并注明本次机器交接未核验，不能伪造通过。

出现状态冲突或内容截断警告时，回读对应原文件。机器提取不能理解所有中文否定式；
可把当前状态写清楚，但必须保留实际失败、待办与未验证项，不能为了得到 `ready` 删除事实。

正常实施、更新计划或产生新提交后，旧材料过期是预期行为。如果仍需接续，
先更新原计划，再用当前 HEAD `prepare` 新材料并在消费前 `check`。
不要为保住旧包而锁住任务、撤销有效改动、改写旧指纹或自动重做已完成工作。
没有交接需要时，不必在每一步生成材料包。

## 首个真实样例：修正 callback 导语

基线 `31d65d5` 的 [callback 文档](../codex-callback.md) 开头仍沿用
2026-10-20 的 MACPIE 待接入方向，与 [2026-10-25 决策](../DECISIONS.md#2026-10-25--围绕-cli-做轻量适配)
早已冲突。本轮按 [2026-11-22 当前决策](../DECISIONS.md#2026-11-22--把开发工作流作为-cm-核心)
更新核心定位；样例只修改该文档的导语、日期和决策链接：

- **R1**：导语以多个 Harness 可复用开发工作流为核心，由宿主原生工具执行，CLI 轻适配按需保留；不再将 MACPIE 列为待接入。
- **R2**：后文 Paperclip 专用桥的原生身份、生命周期、回执与去重边界保持原意。
- **R3**：目标决策链接存在，实际 diff 符合样例范围，`git diff --check` 通过。

由实施者交付 diff，主 Agent 独立回读并把实际结果写入本轮已有计划。
此处定义验收方法；通过结果以实际回读与验证记录为准。
