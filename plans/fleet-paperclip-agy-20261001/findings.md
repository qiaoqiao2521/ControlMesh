# Findings

## 当前边界与取代关系
CM 继续使用 Paperclip 与外部薄适配，不修改上游核心，不重新推广 Orca/旧 Python daemon。旧 CM UV 环境只保留为原 cron 的一次性执行库，默认入口已切换的主机不能再由旧任务重启旧消费者。

用户最新选择：全机只飞书；Telegram 可停，身份/config 保留。AGY 每机不同账号，登录后置。BF/436 有各自既有飞书身份，另外六台缺独立身份/route；程序分发不含认证，不借机器人、不广播、不用 Telegram 兜底。

## 已采用的源证据
- 官方 AGY 固定 1.2.14 包与实际二进制 hash 一致，8 台安装接受。官方 installer 在已有旧二进制时可能 exit0，故以实际 resolved binary/version/hash 判定。
- Paperclip 2026.916.1 的 package engines 是 Node >=24.11.0，早期报告“Node >=20”被直接证据推翻；使用隔离 Node 24.21.0，其他网站系统 Node 不变。compat 历史目录尾号不等于版本，实际 package 为 cm-compat.5。
- 本轮原 registry 四台合计 63 enabled：BF14、greenrise12、colocrossing16、Moonrise21，现已逐项回读为 native active schedule。OS cron/timer 和 disabled 定义分别保留。legacy 已核对实际服务 HOME/loader 和原 UV CLI 的 cron list=[]，确认无有效任务；不是根据标准路径缺文件推断。
- BF 默认 CLI、原生指标任务 CMB-5 和原有只读 cron CMB-7 均实际通过。最后适配代码 `aa2c6d3` 已推送；107 项适配测试及 12 项参数化子测试通过。具体验收与下一步见 [progress](progress.md)。

## 执行契约中实际发现的错误
B1 初始候选的 10 项测试与一次指标成功没有证明周期契约；根独立负向复现了身份读取失败放行、run 多 issue 选错、旧成功产物被接受、启动/评论错误后遗留状态、嵌套独立 session 模型进程漏清理与原始错误上传。最后版本才按真实契约收口：

- 当前 run/context/关联 issue、company/assignee 与 routine origin 明确核对，不 fallback 任意 todo；真实 API 关联字段是 issueId。
- issue 使用合法 blocked，评论与终态回写独立；不能将非法 failed 或 process exit0 当任务终态。
- 只有本轮窗口内的新 artifact 可接受；完整按 run 保存，失败产物保留但不升级成功。不上传 raw stdout/stderr/认证错误正文。
- Linux subreaper、PPid/出生 tick 与明确自有子树解决独立 session 逃逸；不 kill 共享进程组或其他任务。
- quiet 先于模型；原水印加锁原子更新，watchdog 依据明确 native clock/映射/切换时间判断，暂停不算失败，未知不回退旧状态。

## 上游行为须回读验证
1. routine.variables 未在 title/description 中引用时，上游 syncRoutineVariablesWithTemplate 会删掉 definitions。迁移必须包含 `{{cmJobId}}` 引用并回读；API exit0 不是映射已经保存。
2. terminal heartbeat 对应的 blocked issue 不永久占 live execution 槽；release 不按 issue status 分支，error Agent 仍可调用。全部 routine 保留 skip_if_active、single Agent maxConcurrentRuns1、skip_missed，不为错误假设引入 always_enqueue。
3. runner 需 Python >=3.11。复用旧 UV 的合格解释器，通过 process command+args 显式选择，不替换系统 Python。
4. comment 的原生执行关联是 createdByRunId；runId 为空不等于没有关联。完整 artifact hash 与该字段、run.contextSnapshot.issueId 和实际执行窗口一起核对。
5. active 不等于重启后能恢复。根发现 Moon/legacy 新 system unit 尚 disabled，补 enable 后逐机回读 MainPID 不变；退役旧 unit 的停止失败记录留私有恢复材料，不能重启旧消费者来清理 failed 状态。

## 成果与通知的取舍
52 项精确 fleet ops 正常静默；11 项业务按原产物/目标归为 always。分类根据 catalogue/真实 TaskDescription/config，不能从标题、output_policy 或 CLI success 推断。

原 schema 没有 notify_when，现按根审定在原 task.config.delivery 中补明确 anomaly/always/never。原文件缺失时复用旧安全 defaults，不覆盖已有 publish/artifact 设置。direct_result 且 require_review=false 是已有生成授权；其他发布/外部目标仍单独验收。

成功执行先保存本轮完整成果。缺本机飞书路线的业务保持 delivery_pending，不能称 delivered；重试投递复用原成果，不再跑模型。ops 的 success 只证明执行，不能用正文 warning 子串猜风险或宣称主机健康。

两个原来未分类任务已回源：colo daily RSS 要求本地产物/摘要，Moon weekly 要求当周 NotebookLM 与导入计数，always 有依据；缺 sidecar 不能证明 NotebookLM 发布链通过。Moon weekly 原 07:20 与 quiet 至 08:00 的时间边界保留，按实际执行时刻决定是否跳过。

## 执行交接
真实 AGY 已完成程序部署的主要部分，但 B2 因 Individual quota 429 未交齐结果后退出。根采用现有 CLI 接续，以互不重叠的主机 owner 完成收口，并独立验收；不换 Google 账号、不重做已通过 BF 模型任务、不将中间服务状态写成完成。

采用由 Obsidian 开发知识入口定位的 CapMesh PIT-005：共享程序、机器参数、身份运行态分开，程序统一分发而账号与机器人不跨机复制。项目状态留本计划，程序选择/当前方向由既有收尾 CLI 回写 CapMesh，原始运行证据留私有工作目录。
