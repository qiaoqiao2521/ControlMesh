# Progress

## Current
2026-10-01：8 台默认 cm/controlmesh 已统一到各机独立 Paperclip；63 项有效 CM 定时任务全部接管。新服务 active/开机启动，旧消费者 MainPID0；原停用定义、OS cron/timer、身份与配置保留。436 既有飞书入口与公众号 timer 保留。

8 台 AGY 1.2.14 程序更新接受。每机不同账号，登录按用户安排后置；另外六台缺独立飞书身份/投递路线，成果保存在本机待投递。运行接管不扩大为账号、消息投递、完整风险判读或业务发布验收。

## Done
- 8 台实时 SSH/架构与运行归属已核对；AGY 固定官方包及实际二进制 hash/版本一致，436 的实际 agent436 用户另行验证。
- Paperclip 固定 2026.916.1、隔离 Node 24.21.0；上游实际要求 Node >=24.11.0，推翻早期 Node >=20 的猜测。Feishu compat.5 程序包已校验，身份未随程序分发。
- BF 修正版真实指标任务 CMB-5：native run `0da6f774-56ee-4cb6-9e2b-cf0ddef72394` succeeded/exit0，issue done，归属及独立产物 hash 与回执一致。
- BF 原有只读任务 CMB-7：native run `808660d8-ddbf-42e4-b221-61c2f1db5ea5` 经原 Claude/sonnet 执行后 succeeded/exit0、issue done，fresh 完整独立产物 SHA256 `ba1ce2fd311f3e0efbfbf72d6cc7e698dd8563584b4cfb5c47595464feff38c0`，正常无外发。仅证明该真实执行链，不扩大为全部 cron、风险判读或业务发布验收。
- BF 14 个 routine 通过 `cmJobId` 模板变量回读明确绑定原 job；watchdog 实测识别 0 active/14 paused 后恢复 14 个原 schedule。旧 system/user daemon 均 MainPID0，root 5 条 cron hash 保留。
- 最后薄执行器与现有 watchdog 已审查：run/issue/routine 严格归属、本轮 artifact 检查、合法 blocked/失败退出、自有子树清理、quiet 前置、水印加锁。107 项适配测试及 12 项参数化子测试通过，代码已推送 `aa2c6d3`。
- 六台各一次真实无模型指标任务接受；根直接回读 issue/run/company/assignee、执行窗口、独立文件完整 SHA256 与 comment.createdByRunId。默认双 CLI 在 `/tmp`、清除临时覆盖后验证；新 service 实际 Node 执行路径和持久启动、旧 MainPID0 与原 OS cron 前后哈希分别核对。

| 主机 | 原有效 cron → 新 native active | 已接受真实任务 |
| --- | --- | --- |
| bf2025 | 14 → 14 | CMB-5 指标；CMB-7 原 Claude/sonnet cron |
| meiren | 0 → 0，14 项停用保留 | CMM-1；run `e2d52d3f-3481-4167-b51f-13e8905720ce` |
| 436 | 0 → 0，公众号 timer 独立保留 | 既有入口/文本链接受；post 消息复测边界仍保留 |
| qiaobird | 0 → 0，19 项停用保留 | CMQ-1；run `2ef136a3-0147-461d-9710-ff9def3f2634` |
| greenrise | 12 → 12，3 项停用保留 | CMG-3；run `31de5a67-e1be-48df-ae40-a8515bfd432c` |
| colocrossing-ny | 16 → 16，1 项停用保留 | CMC-1；run `81b80856-5906-471d-82b8-4b5d843b6290` |
| moonrise | 21 → 21，4 项停用保留 | CMM-1（独立公司）；run `38e3e80f-c272-4a0d-91fe-cba78fa1a385` |
| legacy-ai-server | 0 → 0，实际 loader/旧 CLI 证实为空 | CML-1；run `295176fe-eb06-4b81-a437-32bcf279aeed` |

- 63 项原时刻/时区、cmJobId 模板映射、skip_if_active/skip_missed 回读；52 项运维正常静默，11 项业务保存成果并保持各自发布/复核策略，缺路由不称已投递。
- Colo 旧三件存量任务实际有产物推进，暂停新增后全部自然结束才切时钟，未杀在进行中工作。Moon/legacy 新服务曾漏 enable，根发现后补齐并回读，MainPID 未变化、未重启。
- meiren 原 CI 轮询曾向旧账号/旧 CM 派发；原定义备份，原 crontab 保留，当前执行入口已显式暂缓并返回 `pending/native_dispatch_not_configured`。没有为已暂缓的旧链新增 Agent/适配器。

## Remaining
- 全机只用飞书；Telegram 可停但身份/config 保留。BF/436 有各自独立飞书身份，另六台尚缺自己的身份与明确投递路线；缺路线只本地待投递，不回退 Telegram/广播/借用机器人。
- 运维风险判读与异常飞书投递、业务完整产物/外部目标/审批分别验收；执行成功不等于主机健康或已发布。
- 各机 AGY 账号映射与实际服务用户登录留待用户配合，本轮不新开 OAuth/PTY、不复制认证。
- 后续接续 owner 为根 Codex；源状态入口是本文件 Current，机器级 context/company/trial/产物 hash/恢复路径在各机私有备份与本机三份 pair 交接中，原始运行日志、认证/OAuth 不入库。

## Issues
早期 B1 的 10 项测试和一次指标成功没有覆盖全部周期契约，根复核发现的失败放行/旧产物/子进程泄漏等已经由最终版本收口；不能沿用旧报告“全部 P0/P1 已全面修复”的判断。过程与恢复依据保留于本机私有工作目录，不入库运行日志、凭据或 OAuth。

Moon weekly 的原 07:20 schedule 与 quiet 至 08:00 存在时间边界；runner 按实际执行时刻判断，排队后可能越过 quiet，不能承诺每周一定生成或一定跳过。本轮保留原语义，不扩大调整时刻。

真实 AGY 已实施主要程序部署，但 B2 因本机 Individual quota 429 退出、未交完整结果。根接续现有 CLI 收口并独立接受；这不是目标机认证失败，也未换 Google 账号绕过额度。

## Next
登录和缺失飞书身份按用户安排后续接续；436 有新用户消息时补 post-path 复测。选中真实业务任务后再验收风险判读/外部目标/投递，不批量触发模型来证明数字。SpecMesh 与 CapMesh 随本批提交交付，通过既有 check/sync CLI 回写，不增加 Action、cron 或常驻 Agent。
