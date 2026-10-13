# Progress

## Current
2026-10-14：新增compat.9启动恢复和纯CLI门禁。本机和六机插件已更新；本机、BF、436、Green、Moon、Cy真实新回复已回读。Cy补齐空chat路由并接入既有native持续私聊，旧任务不重派。436等待在途工作自然结束后发布9，配置、主进程及生产守卫保持。Qia独立配置仍为空，原Codex App桥保留。BF同类缺监听已恢复；发布过程中已纠正官方dev-watcher与HTTP生命周期的竞态。详情见[逐机证据](evidence/fleet-runtime-guard-20261014.md)。

以下10月13日及更早条目保留当时的验收范围，不作为当前恢复指令。

2026-10-13：436 再次不回复。持久配置和 Paperclip 健康，但升级后的 worker 未应用公司配置，实际订阅器缺失。已经官方 API 原样重应用原配置，主进程和配置哈希保持；新消息“436监听恢复验收通过”真实送达。原23:25消息按原 ID 一次补入；第一轮运行十分钟超时，Paperclip已自动沿同一源评论接续，业务结果尚未完成。宿主配置回放的具体失败点尚未确定；升级后实际监听门禁已补入操作说明。[本轮证据](evidence/436-ingress-recovery-20261013.md)。

2026-10-12：本机及六机原插件已统一 compat.8，保留生产修复、完整配置和原 manager 进程。436 新消息、BF 两轮持续私聊实测通过。Green 阻止11条旧源重派，两轮已实际回复“记住了”“薄荷湾”，同一提供商会话、原主聊天各一次；仍保留一条未执行的早期测试 pending。Moon 原 App 凭据被 SDK 拒绝，订阅器已停，安全输入入口已安装。Cy 官方扫码已过期，无创建结果。qiaobird 正常 owner-event → Codex App 桥保留，独立 CM 接入仍未完成。[逐机证据](evidence/fleet-live-20261012.md)区分代码升级、真实送达与恢复入口。

本机审查曾误用旧 cm，短暂启动旧 Python 服务并写入30个旧工作区规则文件；已停旧进程、禁用旧自启动、将 cm/controlmesh 改为官方 Paperclip CLI。缺规则写入前快照，不宣称已恢复。

2026-10-07：外部飞书插件 compat.6 已在本机与 436 升级并完成真实连续私聊验收。源码与 Ops 交接已提交推送，远端回读一致。

## Done
- 使用官方 Paperclip 2026.916.1 原生 Agent Chat，不改核心、不增加调度服务。
- 新增固定原包哈希的构建器、精确 worker 变换、原生 API CLI 与传输回执模块。
- 身份配对、重复事件、generation、未知提交、ACK 和崩溃恢复采用明确拒绝或回读；没有自动模型重试。
- 新增 Python 52、原生传输 Node 30、真实 worker RPC 18 项验证，共 100 项通过。436 现场 worker 的 6 项原生 RPC 验证另行通过。
- [隔离真实 API 验收](evidence/native-api-acceptance.md)覆盖同一原生对话、幂等提交、重置和保留历史，没有真实模型调用。
- [本机实际私聊](evidence/local-live-acceptance.md)：CLI user 发出两个独立新消息，原机器人分别回复“记住了”“竹叶舟”，同一提供商会话，每条一次，主聊天流。
- [436 实际私聊](evidence/436-live-acceptance.md)：原机器人分别回复“记住了”“松果灯”，同一提供商会话，每条一次，主聊天流。
- [436 模型入口](evidence/436-provider-verification.md)：仅更新过期 model 字段，真实 Paperclip → OpenCode 调用通过，进程为 agent436。
- 保留插件 ID、登记路径、机器人、旧任务、cron、已有配置与生产修复。Paperclip 主进程没有重启。
- 436 长期角色的 Article98 单次实验限制移至实验记录，仅显式实验任务使用。
- 独立审查确认最终回复筛选与身份边界；公开资料只包含合成验收口令和必要关联 ID，不含账号凭据或私聊转储。

## Limits
- 当前新私聊入口支持文本；附件给出明确限制提示。
- 问题卡与审批卡提示转 Paperclip UI。UI 回答后的 continuation 来源关联尚未真实验收；不宣称飞书卡片闭环。
- 执行任务完成后的主管独立判断沿用既有协作机制，本插件不新增主管自动唤醒。
- 本机旧 retry 中保留一条发送不确定的历史记录，未自动重发；新入口不进入旧重试队列。
- 原批次仅部署本机和 436；2026-10-12 已逐机接续，实际送达回源本轮证据。meiren 的平台移除决定保留；没有验收的服务器不提升状态。

## Delivery
- 2026-10-14批次：53项插件Python、27项CLI、51项Node、40项真实SDK回归通过；Green/Moon生产候选各28项原生RPC通过。5份本批Markdown的23个本地链接通过。当前实现、运行部署与实际送达分别回源本轮证据；完整配置、私有配对和运行日志不入库。
- CM 实现、测试、非敏感验收证据：[59e3212](https://github.com/qiaoqiao2521/ControlMesh/commit/59e32127f05ce5f45dc77f068580d99d517eed59)。
- Ops 当前 436 交接与模型入口：[dd915e2](https://github.com/qiaoqiao2521/ops-vault/commit/dd915e26c5b72c16e125a385f3e076e893b6fcd5)。87 项测试、完整 pre-commit 与所需文档门禁通过。
- GitHub API 回读两个 main 与推送提交一致。CM 14 份本次文档的 67 个本地链接通过，暂存差异与敏感模式检查通过。
- 生产私有配对、配置快照和运行状态均不入库。以下历史遗留保留在本机，没有混入本次交付。

## Preserved work and handoff

主 Agent 接续 owner 为根 Codex。下列已有有效候选保留在当前本机工作树，尚未纳入本次提交；不能用原生私聊测试替代它们的验收。

| 范围 | 具体阻碍 | 最短接续入口 |
| --- | --- | --- |
| Orca CLI、bridge、探针与 golden 测试 | 已转为历史可选方案；A01–A12 尚未全部通过。大批源码需要按自身计划核对，不能混为 Paperclip 默认入口 | `plans/cm-orca-headless-bridge-v0/{task_plan,progress}.md`；核对 `controlmesh/orca_bridge/`、`tests/orca_bridge/`、相关 CLI 和脚本，再执行其离线检查 |
| tau-bench 实验和 `.gitignore` | 已记录独立分支 `codex/tau-bench-20261001`、提交 `888639a`；尚需比对本地遗留与该交付，明确生成结果边界，不收运行输出 | `experiments/tau-bench/README.md` 与 `plans/tau-bench-20261001/progress.md`，不重跑模型 |
| sandpile 作品与图片 | 任务记录已有本地验证和 Paperclip 附件交付；公开提交前尚需核对二进制、生成结果与许可 | `experiments/sandpile-qia73/README.md`；`node experiments/sandpile-qia73/verify.mjs`；浏览器复验使用其既有脚本 |
| 旧 436 bootstrap 与 cron 委派材料 | 历史部署入口可能重新引入旧 Python/root 或已替换的运行方向，需要逐项比对当前 fleet/cron 记录 | `plans/436-paperclip-feishu/bootstrap.sh`、[委派入口](../runtime-convergence/delegation/README.md)和四份 AGY/cron 材料；先读当前 Ops 手册，不直接执行历史脚本 |

未覆盖或删除这些变动，未盲目暂存全仓。对已验收的原生私聊改动先及时交付，保留各遗留成果的独立接续责任。

## Next
本轮接续：Qia独立CM不借用原桥身份。Cy旧legacy源虽运行成功却未送达，保留原任务及回执待核对，不重派或冒充native验收成功。不要为等待恢复已退役cron。知识收尾 already_covered：既有Wiki“按当前任务选择验收依据”与“远端任务恢复：先确认提交边界”覆盖判断；版本特定问题留在本轮工程证据。旧Orca等保留工作仍按本页owner与最短入口接续。

436原23:25任务的首次超时与自动接续已回读，本轮不替代原Agent业务交付的质量审批；根Codex不再投递同一来源。后续升级先验证公司上下文及唯一监听，再验实际送达。

历史compat.8批次通过121项源码回归与两机各18项原生RPC。当前Moon原身份已实测回复，Cy已有独立App及native实测回复，不再等待旧扫码或重复凭据输入。Green早期测试pending、Qia独立CM、UI continuation、审批卡与执行交接仍保留各自验收边界，不增加常驻Agent或定时ping。

## 2026-10-08 基线与待接续

六台继续运行的 VPS 已回读普通用户 Paperclip 基线，冗余 cron 按 Ops 当前清单治理。AGY 公共程序统一1.3.1，普通用户 AUTH 六机仍待完成；qiaobird／cy 独立新机器人尚未创建。Moon 原 AGY 保持 paused，不能把插件ready写成原私聊已回复。

可选cm-agy已完成独立离线审查及上游process任务关联修复，163包装器测试通过，未部署；新handoff不兼容cm-consult既有prefix。根Codex负责实际AUTH与native父任务/交接验收；不更换436已有compat.6生产worker。

当前非root/cron事实回源Ops-Vault，当前公众号任务回源内容仓。旧Orca／tau／sandpile与既有未核实脚本按前述具体owner和恢复入口保留，不纳入本次生产部署；缺原任务验收/发布边界，不能仅凭源码存在推送为已交付。

知识收尾：already_covered，既有Wiki「按当前任务选择验收依据」已覆盖本轮独立判断。上游版本特定字段差异记录在候选说明，不新建知识机制。

## 2026-10-09 CLI 收口

436 公共 cm-paperclip 显式设置 PAPERCLIP_CONTEXT 为 /var/lib/agent436/.paperclip/context.json。实际 agent436、HOME 和 cwd 下 cm status 返回 exit 0、status ok；不再从 root cwd 命中旧 context。该入口仍只做透明转发，不新增状态或模型调用。

436 内容仓通过离线 bundle fast-forward 到 84883d9061fa8c2ef19fbf41eff4c3fbc7900036；交付代码逐字节一致，原辅助脚本和稿件保留，公众号 timer 继续 disabled/inactive。Ops 继续记录逐机 CLI 的真实用户、AUTH 与废弃 root 配置清理；qiaobird Codex 的新登录不提升为全六机 AUTH 通过。

## 2026-10-12 接续验证与交付

compat.8 源码、七处部署、真实收发和误用旧入口的恢复证据见 [本轮记录](evidence/fleet-live-20261012.md)。本轮代码121项回归、两处生产候选各18项 native-only RPC、Moon诊断8项与安全输入15项通过。CM本批9份Markdown的14个本地链接、限定敏感模式和普通文件diff检查通过，统一diff补丁按其格式边界检查；Ops完整pre-commit的11个hook全部通过。生产配置快照、凭据和私聊转储不入库。

知识收尾 already_covered：既有 Wiki「远端任务恢复：先确认提交边界」「按当前任务选择验收依据」与认证迁移边界已覆盖；版本差异留在本轮证据，不新增常驻机制。原有 Orca、tau、sandpile、状态 CLI 和历史部署材料按本计划具体恢复入口保留；本轮没有盲目暂存全仓。同期另一主 Agent 的 callback 准则修复已独立交付，未混入本轮提交。
