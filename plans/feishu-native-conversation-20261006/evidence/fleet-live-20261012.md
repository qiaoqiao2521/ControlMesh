# 六机飞书接入与失联检查

2026-10-12，Asia/Shanghai。范围：BF、436、qiaobird、Green、Cy、Moon。
meiren 与 legacy 不部署。六机保留官方 Paperclip 2026.916.1、原实例与机器人身份。
436 使用 `agent436`，其他五机使用 `cm-agent`，实际 manager 均为 UID 1000。

## 当前结果

| 主机 | 本轮结果 | 未完成边界 |
| --- | --- | --- |
| 436 | 原机器人收到新消息，在主聊天实际回复；插件已统一 compat.8 | 历史失联原因未复现；AGY AUTH 另验 |
| BF | 原「避风港」两轮记忆与回复通过；插件已统一 compat.8 | AGY AUTH、复杂业务另验 |
| Green | 原「如酥」已实际回复新消息；compat.8 阻止旧源重复派发 | 两轮记忆与主聊天送达通过；一条早期测试记录仍 pending |
| Moon | compat.8；SDK 明确拒绝原 App 凭据，订阅器已停 | 隐藏输入工具已安装；需本人更新原 App Secret 后实测 |
| Cy | compat.8 ready，公司配置为空；官方扫码 flow 已过期，无创建结果 | 本人准备好后重新创建单个扫码入口，再绑定与实测 |
| qiaobird | compat.8；既有 owner-event → Codex App 桥有11项 done/sent、单次 ACK | 独立 CM 机器人尚未绑定，不能计为 CM 私聊完成 |

qiaobird 现有 App 的 WebSocket 保持。不能为接 CM 再启动第二个订阅者。
本机既有连续私聊验收保留，插件也已升级 compat.8；本轮没有重复模型测试。
程序版本、AGY 原生 AUTH、模型请求与飞书回复分别判断；本轮不提升普通用户 AUTH 状态。
原63项 routine 的退役结果沿用 Ops，未恢复定时任务、Notebook 消费或模型 ping。

## 插件统一与验证

固定原包 SHA256：`dac91409329a4005e12b59c0bf17c357a17fc7c0e7998a093624a1c289850cf3`。
compat.8 源码通过 Python52、原生传输 Node39、真实 SDK worker RPC30，共121项验证。
Green、Moon 现场候选各通过18项 native-only RPC。之前已有42项生产回复守卫验证。
完整 RPC 的旧完成事件用例不适用于两机更严格的生产守卫；该尝试失败后改用限定的 native-only 验证，没有将其记为通过。
Moon 原 AGY collector 保留准确字节，独立业务路径未重新验收。

七个部署 receipt 见 [版本、配置与进程回读](fleet-plugin-deployment-20261012.json)。
仅原子替换五个已核对的插件文件，经官方 `POST /api/plugins/:id/upgrade` 重载。
各机 manager PID、启动时间、UID、公司集合和完整配置哈希保持；观察窗口内无新增运行。
升级程序没有请求模型或发送飞书消息。真实聊天测试另计，不能从 ready 推断送达。
Green、436 保留当前生产回复守卫；Moon 还保留固定会话与原 AGY collector。

| worker 类型 | 主机 | SHA256 |
| --- | --- | --- |
| 基线 | BF、Qia、Cy、本机 | 65d749914e0723c27d445a76e0ea524f1f956266cd5c3ab8ceac6ae0b9d06b3f |
| 生产回复守卫 | Green、436 | ebac646a99699803a76c0e6723d63dcb1a7b0260fc3184bcb33207cdf984d4b8 |
| 固定会话与 AGY collector | Moon | d6c3aa150e6fc6c8a1add5dc9b0192b663a606a41bb7d0f3abf681d510442646 |

Green 首次 compat.6 升级遇到官方重复 starting 登记而进入 error。
官方 disable 在 error 态返回400；随后合法 error→enable 恢复 ready。
未直接改数据库，也未证明该生命周期竞争已持久修复。
Cy 首次经官方 install 加载；原登记 ID、路径在后续升级中保留。

## 436 新消息

源消息 `om_x100b63fd871b9490b4b968ccdf1a6b9`，合成要求“只回复：436收发验收通过”。
运行 `15c16448-5365-439f-9e7d-9c729bc512ec` 成功，exit0。
实际回复 `om_x100b63fd83b910a4c28590522a4c668`，内容一致、原 App、主聊天。
这次实际收发先于 compat.8 统一升级。10月7日两轮持续会话证据独立保留。

## BF 两轮持续对话

第一轮源 `om_x100b63fdb43e70a0b265f674ba69023`，要求记住“青石桥”。
运行 `639a36cf-6aef-4ae9-b0e0-d3012bd4a977` 成功；回复 `om_x100b63fdb33ad88cc22090bd65f42e5`，内容“记住了”。
第二轮源 `om_x100b63fe48e604bcb103af4994a63f1`，询问上一轮代号。
运行 `9d3eb667-f9c5-4b92-b7c1-dce51a9ad2ef` 成功；回复 `om_x100b63fe4787e0b4df31e0087f97063`，内容“青石桥”。
两轮使用同一非空提供商会话和原生 issue `a4649700-25aa-4c1d-ad81-22f22b934cb4`。
原「避风港」App，两个主聊天回复各一次，thread 为空。
实际收发先于 compat.8 升级；升级后的配置哈希保持。

第一次配置尝试使用非法 replyMode=reply，POST400 未生效。
随后一条测试走旧任务线程，不能算原生验收。纠正为 message 后才接受上述两轮。
生产配对归运行用户，0600；不发布 owner 身份或完整配置。

## Green 重放根因与恢复

compat.6 将 native 入口放在旧 session/dedup 判断前，11条已有旧送达回执的源消息误入新队列。
评论 author=local-board 来自原生桥接，不能据此认定为网页新任务。
独立核对原源消息、旧 run、非空 reply ACK 后，用官方 issue tree hold 停止重复队列。
最后旧11项为5次重复执行完成、6次取消；暂停后这些旧源没有新增运行。
原历史与此前已产生的重复回复保留，不伪称本次修复避免了所有重复。

原生 issue `568d548d-7859-400a-b419-27045692e6c8`。
释放 hold 时 wakeAgents=false；原生 `/new` 运行 `61418208-9925-4110-82a9-ee1ac80c64a0` 成功。
重置评论 `9cc92c0b-43bb-4712-8ee3-cdb66c3083ed` 进入 generation1；usage为空，没有提供商模型调用。
临时关闭 native 与 subscriber 后恢复原完整配置，私有快照留在服务器。

compat.7 先查已有 native receipt，再只读旧 admission。误入 pending 的旧源标为 legacy_retained，保留实体与历史。
随后发现8条旧源属于原 Agent，3条属于当前 Agent；拒绝旧 Agent 会阻断整个 flush，包括已经成功的新模型结果。
compat.8 通过官方只读 Agent/Issue 查询核对旧公司归属，继续保留旧 ownership。缺失或跨公司记录仍明确拒绝。
Scoped wrapper 已提供 companyId=scopeId，不需要修改旧实体数据库字段。

17:59独立回读：旧11项为6个原有 delivered、5个 legacy_retained；旧源 pending=0。
总 pending 仍有1条早期合成测试 source12：`om_x100b63fe490180a4b30290a62725572`。
其评论 `366bd3d7-bf4f-4d72-8333-5aa8c2114e5a` 的 generation=NULL；wake已取消，无执行、无回复。
保留 phase=submitted，不重发、不直接改库或删除评论。此测试传输记录不阻碍已验证的新回复。
根 Codex 接续：若官方可证明其已 superseded，再沿现有回执恢复；不能用时间推测已失效。

### 新消息实际送达

源 `om_x100b63fef1dab8b4b3c4b1ff64f6d86` 要求记住“薄荷湾”。
原生评论 `6807b994-c143-41ed-8815-4d7a69701d03`，generation1。
运行 `ff65775c-361c-43f5-8501-9699d3dfe76f` 于09:46:52Z成功。
提供商会话 `ses_ed07eb992ffecLygemRJlyHRhU`；最终评论 `134815a4-9fc9-4ab1-bdd3-2abd31ee4720` 为“记住了”。
compat.8 恢复旧队列核对后，复用该已成功结果，不再次调用模型。
09:57:37Z 持久 ACK 为 `om_x100b63febfdcbca0b301d7b2132ef2a`。
本机 user CLI 平台回读同 ACK、原 App、内容“记住了”、主聊天 thread为空。
第二轮源 `om_x100b63ff44d7c4b4b32ce3440aa30a0` 于18:04:17发出。
运行 `91a154ac-3f15-46c2-8143-942b06129dc5` 成功，exit0；提供商会话前后均为 `ses_ed07eb992ffecLygemRJlyHRhU`，与第一轮一致。
最终评论 `0ccc800f-2733-49dc-8bdf-c0226f4a16f2` 的作者与执行 run 匹配。
持久 ACK 为 `om_x100b63ff5ac318acb325e7efbb8afee`；本机 user CLI 独立回读内容“薄荷湾”、原 App、主聊天、thread为空。
平台最新五条中两轮各一个源消息和一个回复，与两个原生 ledger 和关联 run 匹配。
18:08独立只读复核仍仅 source12 pending，无其执行或回复。

## Moon 根因与安全输入

SDK lark-oapi1.7.3 报 ClientException 1000040345，精确凭据拒绝转换为 credential_invalid=true。
原启动器吞掉异常链。诊断补丁与输入/输出哈希见 [诊断材料](moon-sdk-diagnostics/README.md)。
八项离线测试覆盖敏感异常过滤、非阻塞 PIPE 排空和0.5秒退出上限，补丁已部署。
模型切换和插件升级不能修复凭据拒绝。原「月神」App、聊天和加密 store 保留。
native 私聊已改到普通主 OpenCode；旧 root cwd AGY 仍 paused。
enableEventSubscriber=false，活跃订阅器0；本轮不发送无效验收消息。

原 App 安全输入入口 `/opt/cm-feishu-moonrise/rebind_secret.py` 已安装。
15项离线验证及现场现有库接口、缓存键、锁与权限核对通过；本人尚未输入，不声称已恢复。
本人在 [现有终端入口](moon-sdk-diagnostics/README.md#原-app-安全输入) 隐藏输入原 App 当前 Secret。
仅验证同一应用身份后更新原加密 store；不另建机器人、不经聊天传递 Secret。
保存后由根 Codex 恢复原订阅器，并独立实测接收、原生运行及原私聊回复。

## 本机旧入口误用与纠正

一次审查误用旧 `cm plugin health`，短暂启动旧 Python CM 并改写其私有工作区规则。
本次启动的旧进程已停止；原 controlmesh.service 已 inactive/disabled，无旧 CM 进程在跑。

### 30 份规则的取证范围

`~/.controlmesh/logs/agent.log` 记录 2026-10-12 实际 5 次规则部署：16:25:42、16:26:53（两次）、17:23:13、17:23:17。
历史累计 52 次 `Deployed 30 rule files`，跨 9/29、9/30、10/1、10/2、10/4、10/5、10/6、10/9、10/12。
即旧 CM 每次启动都重写这批文件，本轮不是首次改写。

部署器是 `controlmesh.workspace.rules_selector`，第 217 行用 `shutil.copy2(template, destination)`。
copy2 保留模板 mtime，所以 30 份里多数文件 mtime 停在 2026-09-11 08:28（uv 安装时刻），只看 mtime 会漏判。
真实写入由 ctime 暴露：非任务规则文件 ctime 均为 2026-10-12 17:23:17，任务子目录文件未被本次触碰。

逐字节比对 29 个非任务规则文件与包内 `_home_defaults/**/RULES*.md`：
27 份完全一致；仅 `workspace/AGENTS.md` 与 `workspace/GEMINI.md` 不同。
两份的差异只是模板 `{{CONTROLMESH_TASK_DELEGATION_POLICY}}`（模板第 90 行）被现有配置展开填充，
属同一渲染流程的确定性输出，不是另一份内容。

结论：报告已比对的 29 个非任务规则文件与包内模板及当前配置渲染一致；历史日志说明重复部署早已存在。
当前一致性不能反推写入前没有独有修改。缺少写入前内容快照，旧规则原文恢复仍未验证，不能据此断言没有内容损失。
2026-10-13 收口审查据此纠正“取证结清”的过度结论；当前入口清理与历史内容恢复分别判断，不恢复旧模板作为默认入口。

本轮 41 份规则文件已快照到 `~/.controlmesh/_rewrite-snapshot-20261012/`（保留原权限与 mtime），供后续比对。

报告另记录 17:23:14 `skill_sync` 删除三个 symlink，原指向仍需依据历史记录判断：
`~/.claude/skills/skill-creator`、`~/.codex/skills/skill-creator`、`~/.gemini/skills/skill-creator`。
它们指向旧 CM 包，旧 CM 退役后本就不适用；系统官方 Skill Creator 仍可用，不重建旧链接。

### 复发入口已消除

本机 cm/controlmesh alias 已修正到官方 Paperclip CLI，`cm health` 实际返回 status=ok、version=2026.916.1。
旧 Python CM 包 `~/.local/share/uv/tools/controlmesh`（controlmesh 0.43.0，146MB）经本人确认后移除，
与其他五机口径一致。移除前已核实无依赖：crontab、systemd 用户单元、`~/.config`、`~/.local/bin` 脚本均不引用该 venv；
唯一关联的 `controlmesh.service` 已 disabled 且 ExecStart 指向 `/home/muqiao/.local/bin/controlmesh`，
该路径早已改指 Paperclip，删除后不会留下可执行旧入口。

移除后复核：目标路径已不存在，`~/.local/share/uv/tools/` 只剩 ansible-core、google-colab-cli、huggingface-hub；
`cm health` 仍返回 2026.916.1；controlmesh.service 仍 inactive/disabled；无旧 CM 进程。

## 接续与知识收尾

根 Codex 接续 Moon 原凭据输入、Cy 新扫码、Qia 独立 CM 身份，以及 Green 测试传输遗留。
Cy 已过期 flow 保留；app.json 不存在，不把过期当作创建成功。本人准备好后按单机流程重新开始。
原 owner-event 链继续保持；独立 CM 接入不能抢占已有 WebSocket。
Ops 当前六机表和问题清单同步更新。新消息送达、旧遗留恢复和 AGY AUTH 各有边界。

2026-10-12 续跑复核：上述四项远端状态与交接一致，已实测 Moon 上 `/opt/cm-feishu-moonrise/rebind_secret.py`
存在且 paperclip feishu worker 在跑；Cy 上无 `/opt/cm-feishu-cyrise/`、无 app.json，确认过期未产出。
本机当前规则与模板的对照范围见上节；历史原文恢复仍未验证，接续 owner 为根 Codex，最短入口是已留存快照与原规则来源。
本机旧 Python CM 包移除按上节记录完成，不再列为待删除；Moon Secret 输入与 Cy 重新扫码仍待本人操作。

already_covered：沿用 Wiki「跨机器迁移：先判断资料属于哪一层」「按当前任务选择验收依据」与「远端任务恢复：先确认提交边界」。
单机状态留在 Ops，版本补丁与合成消息证据留在 CM；本轮不新增知识机制。
其他进行中工作由其原计划 owner 接续，未覆盖或纳入本轮提交。

## 最终文档门禁

CM 本批9份 Markdown 的14个本地链接、限定敏感模式和普通文件 diff 空白检查通过。统一 diff 补丁保留空行的 context 前缀，单独按补丁格式检查；不删除这些必要空格。Ops 完整 pre-commit 的11个 hook全部通过，包括111项仓库回归、frontmatter、links、vault、静态语法和两个生成索引检查。独立只读审查确认七份 compat.8 部署记录与原 receipt 一致；代码升级、真实聊天与凭据修复未混为同一验收。
