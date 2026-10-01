# 关键决策会审 v1

CM 是工作流与薄适配，Paperclip 是运行底座。本功能不是通用 graph 引擎，默认不参与普通任务。
选型、较大改动或重要发布判断需要独立意见时，才显式启动。

## 从 SO101 会审保留与改进什么

保留：共同基线、主协调者先写初判、各 CLI 真实身份、引用、实质分歧、独立裁决。
改进：直接调用 CLI 改为原生子 Issue；partial/失败不算完整意见；补取与复核共用一个追加槽位；
恢复从原 Issue 和回执接续，不重新启动整场；未知成本不补零。不改机器人训练方案。

## 边界

- 两个初始咨询子项 + 最多一个追加子项。追加可用于失败补取或定向验证，二者不能各获得一份预算。
- 这是**CM 派发槽位上限**，不是供应商内部 turn、模型请求数、原生自动恢复或 token 的硬上限。
  使用已配置的有超时与权限限制的 Agent；其内部重试/费用策略须独立核验。
- 初判不发给首轮工作者，同一事实包与冻结基线发给两者。这是上下文分离，不是进程/文件隔离；
  共享身份/工作区仍可能读取彼此材料。无写权限要求应由实际执行环境落实，不能靠提示词保证。
- 只复用 Paperclip `children`、`blockParentUntilDone`、Issue、comments、heartbeat runs。
  原生任务负责等待与唤醒，命令一次性返回，不轮询、不调用模型、不新建任务生命周期。
- `done` 表示交接完成。汇总核对公司、父子 Issue、分配 Agent、冻结描述、评论作者与 run 归属；
  结论只记录在私有回执，不自动完成父任务、发布代码或修改其他项目记忆。
- 原生状态仍是唯一执行事实源。回执仅保存冻结输入、槽位→Issue 映射与裁决。
  每场使用一个专属父 Issue 和固定目录；不要复制回执、重建目录以重置预算。
  本机文件锁仅串行化同目录操作，不宣称能约束恶意本机用户或其他 board 操作者。

## 使用

仓库源码入口（无需旧 Python CM）：

```sh
sh scripts/paperclip/cm-paperclip consult --help
```

部署了同目录两个脚本的 Paperclip 薄入口可用 `cm consult`。仅复制旧 `cm-paperclip` 不包含此功能；
已有本机旧 Python `cm` 不会被本次自动替换，避免改变其他命令。
本机独立命令 `cm-consult --help` 对应同一脚本；后文 `cm consult` 可直接替换为 `cm-consult`。

先通过 Paperclip 原生入口创建专属父 Issue 并分配协调者；选定两个不同的既有 Agent。
准备私有 `spec.json`，不要提交真实咨询或凭据：

```json
{
  "company_id": "COMPANY_UUID",
  "parent_id": "PARENT_ISSUE_UUID",
  "coordinator_id": "COORDINATOR_UUID",
  "workers": ["WORKER_A_UUID", "WORKER_B_UUID"],
  "question": "哪个最小方案更合适？",
  "baseline": "仓库标识与固定 commit/dirty diff 摘要",
  "facts": "已核实事实与来源；不要夹带期望答案",
  "initial_judgment": "主协调者独立初判，首轮工作者不可见",
  "constraints": "只读咨询，不实现、不发布；现有资源与非目标"
}
```

以下以 `cm consult` 简写源码命令；目录放本机私有数据区或明确 Git 忽略区：

```sh
cm consult --directory "$CONSULT_DIR" init spec.json
cm consult --directory "$CONSULT_DIR" dispatch
# 协调者结束本轮。Paperclip 处理原生阻塞与事件唤醒。
cm consult --directory "$CONSULT_DIR" collect
```

API 默认只访问 `http://127.0.0.1:3100`，可用 `PAPERCLIP_API_URL` 指定其他 loopback 端口；
远程 URL 和重定向拒绝。认证使用原生环境变量，不读取/复制 provider 登录，不把 key 写进参数或文件。
本工具不读取 Paperclip CLI context；使用非默认实例时须明确 URL，不能假设与原生命令 profile 相同。

工作者按子 Issue 描述产出结构化结果：`revision`、`slot`、`completeness`（complete/partial/failed）、
`recommendation`、`evidence`（引用数组）、`uncertainties`、`usage_tokens`、`session_id`；未知值为 null。
结果必须通过其**真实原生 run**提交，不能由 board 代写再伪装为 Agent：

```sh
cm consult --directory "$CONSULT_DIR" submit initial-1 result.json
```

若工作者无回执目录访问权，可按子项描述经原生接口发表 `CM-CONSULT-RESULT-V1` + 换行 + JSON 评论并完成子项。
完整性为提供者声明，引用是否支持结论仍由主协调者检查。不会自动从流式半段回复猜出完整结果。

初始子项均结束后，协调者可选择唯一追加：

```sh
cm consult --directory "$CONSULT_DIR" followup WORKER_UUID '具体分歧、新增证据与要回答的单一问题'
cm consult --directory "$CONSULT_DIR" dispatch
```

不追加也可直接裁决。追加结果可替代该参与者的不完整首答用于当前判断，但历史首答仍保留。
真实 CLI session 续接由其原生适配器负责；本命令不自动实现跨子项 resume。

## 裁决与恢复

`collect` 返回可比较 `snapshot_digest`。主协调者独立核验后提交 decision JSON：
`snapshot_digest`、`outcome`（recommend/reject/checkpoint）、`rationale`、`dissent`、`next_action`、
`verified_evidence`（引用数组）。

```sh
cm consult --directory "$CONSULT_DIR" decide decision.json
```

`recommend` 要求两位参与者有效结果完整、子项 done、对应 run succeeded，以及协调者记录独立证据。
允许意见相反；不计算多数票。缺席、失败或未完成保留为 checkpoint，不声称完整会审。
每次裁决重新读取原生证据、比较摘要；这不是跨系统原子事务。回执固定的是所见版本，
后续实施仍需核对当前项目基线。引用存在不等于证据已被程序验证。
原生完成事件可能不止一次：本机无模型验收见到 `issue_children_completed` 与
`finish_successful_run_handoff`。重复唤醒应先 collect/读取已记录裁决，不直接重复咨询。
`reported_usage_complete` 只说明提交包里的计数是否齐全，不包含未报出的内部重试或整场总费用。

创建超时/返回异常时保留 `creation_attempted`，拒绝自动重建。操作者从原生任务列表定位确实创建的子项后：

```sh
cm consult --directory "$CONSULT_DIR" bind initial-1 CHILD_ISSUE_UUID
cm consult --directory "$CONSULT_DIR" dispatch
```

绑定会重新校验精确父项、公司、Agent 与冻结描述；不存在或不匹配不能绑定。
若确认上游从未创建，v1 停止此场，由人工核验后另开新场，不提供危险的强制清预算开关。
worker 失败/超时而没有合格评论时，用 Paperclip 原生 cancel 结束相应子项，再 checkpoint 或用唯一补充槽。
不要让自动修复反复消费模型来填齐意见。

## 验证

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider \
  --confcutdir=tests/paperclip_adapters tests/paperclip_adapters
uv run ruff check scripts/paperclip/cm-consult tests/paperclip_adapters/test_cm_consult.py \
  tests/paperclip_adapters/consult_native_probe.py
```

原生无模型协议探针需显式运行，会创建独立测试公司/3 个 process Agent/任务，最后暂停测试 Agent；
不要对已有公司测试或将它当日常命令。入口 `tests/paperclip_adapters/consult_native_probe.py probe <private-dir>`。
真实验证结果与未覆盖边界见[任务进度](../plans/decision-consultation-v1/progress.md)。
