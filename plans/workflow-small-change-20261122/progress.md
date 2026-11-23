# Progress

> 历史记录：以下保留原任务日期与验收范围，不是当前待办或机器状态。文中的历史文件链接固定到清理前提交；当前方向见 [PROJECT.md](../../PROJECT.md)，当前验收见 [本轮进度](../cm-usable-orchestration-20261124/progress.md)。

## Current

首版实现与本地验收完成。

## Done

- 增加标准库 `controlmesh.workflow` 的 `prepare` / `check` 和 `cm-workflow` 命令入口，直接组合独立 SpecMesh 原生 handoff 接口。
- 新增一份工作流文档，统一当前方向与计划入口；既有 Runtime、CLI 调用、通知桥及已部署服务保持原边界。
- 修复 callback 过时导语作为真实小改动样例；当前外部派发说明对齐既有“默认仅 Qoder、AGY 仅显式人工前台”规则。
- 现有 product-layer CI 增加新接口集成检查，锁定 SpecMesh `1e19bdf8093b57326cbadfa7cd9026b033c000ba`。旧 runtime-core 的 `d393c548a2a58989d65e6cdbd60a36e9a81a444f` 保持不变。

## Evidence

当前范围和验收要求见 [task_plan.md](https://github.com/qiaoqiao2521/ControlMesh/blob/851d78b8989d07281d0082a5105f878a99f589c8/plans/workflow-small-change-20261122/task_plan.md)，源代码调查见 [findings.md](https://github.com/qiaoqiao2521/ControlMesh/blob/851d78b8989d07281d0082a5105f878a99f589c8/plans/workflow-small-change-20261122/findings.md)。本轮从 ControlMesh `31d65d540711f429fe583675ad090e40f562f4f3` 开始，源代码及记录随同一变更交付；远端提交以 Git 的 main 引用为准。

## 实际验证（2026-11-22）

| 检查 | 实际结果 |
| --- | --- |
| `CM_SPECMESH_TEST_ROOT=/path/to/specmesh python3 -B -S -m unittest discover -s tests/workflow -v`，独立 checkout 为上述 `1e19bdf` | 10/10 通过，包含 6 个适配边界单测与 4 个真实 SpecMesh CLI 集成测试 |
| 未设置 `CM_SPECMESH_TEST_ROOT` | 6 个单测通过；真实集成类明确 skip |
| 显式配置不存在的 SpecMesh 目录 | 退出 1，不降级为 skip |
| `ruff check controlmesh/workflow.py tests/workflow/test_workflow.py`，使用 uv.lock 的 Ruff 0.15.13 | 退出 0 |
| `python3 -B -S -m controlmesh.workflow --help` | 退出 0 |
| `git diff --check` 与本轮 Markdown 相对链接、7 处新决策锚点检查 | 通过 |
| CI YAML 解析及两份独立 SpecMesh pin、步骤顺序核对 | 通过；新标准库检查在运行时依赖安装前执行 |
| 独立代码与文档审查 | 未发现本轮阻断问题；另做 6 项定点边界检查通过 |

真实接口测试在独立 CLI 进程中生成、保存并重新消费普通材料文件；也覆盖 stdin 消费。所选文件字节变化、HEAD 改变、旧 expected-head、调用方省略原 scope 和材料文件软链接均被拒绝。更新原记录并重新 prepare 后可继续，测试仓库状态未被入口修改。

业务反例：合成任务要求产物为 `4`，worker 自报通过，真实产物为 `3`。材料检查可以通过，但声明仍是 `asserted_candidate`，独立业务断言仍拒绝错误产物。没有把 `executable` 改名为业务成功。

独立审查的 6 项额外检查：篡改目标并重算包指纹仍被 live reconstruction 拒绝；独立 task 不符拒绝；所选产物链接到仓库外拒绝且不泄正文；`executable=true` 与 error issue 并存拒绝；`verified` 与 `executable` 矛盾拒绝；NaN JSON 拒绝。它们是本轮定点检查，不冒充新增的长期回归用例。

## callback 真实样例

主 Agent 对照起始提交独立回读 `docs/codex-callback.md`：

- R1 通过：导语按 2026-11-22 工作流方向更新，明确宿主原生执行；不再将 MACPIE 列为待接入。
- R2 通过：从“下文 `cm-codex-callback`”开始的后续正文与基线字节相同，原身份、生命周期、回执和去重语义保持。
- R3 通过：新决策标题存在，改动仅为该文档导语和日期，`git diff --check` 通过。

在本次实际 CM 工作树上运行以下命令；`CM_ROOT`、`SPEC_ROOT`、`MATERIAL` 分别指向显式仓库、上述独立 SpecMesh checkout 和计划树外的私有材料文件：

```sh
python3 -B -S -m controlmesh.workflow prepare \
  --repo "$CM_ROOT" --task plans/workflow-small-change-20261122 \
  --specmesh-root "$SPEC_ROOT" \
  --expected-head 31d65d540711f429fe583675ad090e40f562f4f3 \
  --scope docs/codex-callback.md > "$MATERIAL"

python3 -B -S -m controlmesh.workflow check \
  --repo "$CM_ROOT" --task plans/workflow-small-change-20261122 \
  --specmesh-root "$SPEC_ROOT" --scope docs/codex-callback.md \
  --handoff "$MATERIAL"
```

成功试跑：prepare 退出 0、`state=ready`；新进程 check 退出 0、`verified=true`、`executable=true`。覆盖显式任务及文档、AGENTS/PROJECT/架构/决定，`outside_scope=unknown` 保持。材料保存在计划树外，不提交运行数据。后续记录更新或提交会使该次材料过期；再次接续须换成当前 HEAD 重新生成。

## 已观察限制

- 首次真实工作树 prepare 退出 3：Current 的“正在集成，尚未完成”被上游关键词分类同时识别为进行中和完成，产生 `declared_status_conflict`。改为明确的“候选实现验证中”后通过，未删除未验事实。此为当前 SpecMesh 的语言提取限制，CM 原样保留拒绝。
- 当前决策文档提取出 450 条陈述，超过 200 条材料输出上限；prepare 保留 `state_statement_limit` 警告。相关决定仍需回读原文件，不能将材料称为完整历史。
- 结果证明本地标准库入口、真实 SpecMesh 与跨进程材料交接。没有实际调用两个不同厂商 Harness，也未验 Windows、跨机器、原生会话迁移、后台恢复、配额或已有部署。
- 本轮未运行整个历史 CM Runtime 测试集；新增测试已接入现有 CI。远端 CI 结果单独回读，不从本地检查推定全绿。

## Next

在下一项真实开发任务中复用本流程，按实际交接需要记录接续效果。
