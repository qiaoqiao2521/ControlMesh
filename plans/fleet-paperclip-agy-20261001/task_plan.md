# 服务器 CM 批量迭代与 AGY 更新登录

## Goal
2026-10-01 用户明确要求现在开始，由真实 AGY CLI 执行所有服务器 CM 迭代，并完成 AGY 登录；先统一下载安装更新。这取代前一轮“10 月 2 日再开始”的时间安排。

CM 使用已选 Paperclip 底座与薄适配，不改上游核心，不继续修补旧 Python/Orca。

## Scope
Ops-Vault 当前服务器组：racknerd-bf2025、meiren、racknerd-436b0c0、qiaobird、greenrise、colocrossing-ny、moonrise、legacy-ai-server。每机以实时 SSH/运行证据确认；不可达不计完成。桌面、开发板不纳入。

目标机现有机器人身份、有效 cron/timer、模型/账号配置、仓库及运行数据保留。用户已确认全机只用飞书，Telegram 可停用但保留身份与配置；须先接好有效 cron 的新归属，再停旧 daemon。禁止同 bot 新旧双消费者；恢复先停新，再还原旧。

AGY 登录每台服务器绑定各自不同的账号。程序包可以统一分发，身份不可统一登录或跨机复制。尚未选定的账号等待用户明确映射；有认证的用户也须确认属于该机，不将 root 的登录等同于实际服务用户的登录。

最新安排：用户选择登录不急，先推进其他迁移工作。436 agent436 的未授权 PTY 已退出，未选择账号、未提交授权。账号映射及逐机登录留待用户配合，不阻塞 CM/cron 迁移。

## Steps
1. [x] 从现有 inventory 确认主机可达性、架构与实际 CM/AGY owner；源材料保留在本机私有 work 目录。
2. [x] 固定并校验 AGY 最新官方版本包，统一下载安装；准备已验收 Paperclip/compat.5/薄 CLI 所需版本与程序，身份不随程序复制。8 台 AGY 1.2.14 安装经独立验证；Paperclip 须使用 >=24.11.0 的隔离 Node。
3. [x] AGY 实施主要程序部署；本机额度退出后由根协调现有 CLI 接续，逐机完成默认入口及 63 项有效定时任务接管。首台真实任务接受后才推广，存量工作自然完成后才停旧时钟。
4. [ ] 按用户安排后置：各机不同账号，由实际服务用户登录；不复制认证、不现在新开 OAuth/PTY。需要用户配合时再集中安排。
5. [x] 根 Codex 独立检查各机命令、服务、保留项和实际执行结果；事实回写并随本批 Git 收尾交付。CM 当前状态由既有 check/sync CLI 同步 CapMesh，具体交付 SHA 以本批 Git 历史为准。

## Acceptance
版本更新、认证可用、CM 命令默认切换、机器人实际收发分别判断。服务健康或 exit 0 不替代实际调用；CLI 默认不推断机器人默认。飞书新消息缺用户事件时留下最短验收入口，不制造群聊噪音。

## 主 Codex 阶段审定
- 阶段 A 接受：8 台真实入口、AGY 1.2.14 与程序哈希一致；436 的 agent436 安装另行验证。认证未随安装接受。
- 首台 bf2025：默认 cm/controlmesh 在普通 cwd、无临时环境覆盖下实际指向本机公司；Paperclip 服务使用独立 Node 24.21.0。原 5 条 root cron 哈希保留，旧 daemon 没有运行。
- 阶段 B 首份 cron runner 拒绝：真实 API 返回 issueId 却读取 id、非法 failed issue 状态、旧/缺失产物及未知任务假完成等边界已独立复现。进程 succeeded 不等于业务完成；受控任务实际 blocked。
- 已暂停 bf2025 的 14 个新 schedule trigger，复查 enabledAfter=0；恢复依据留在该机私有 `/root/.paperclip/fleet-migration-20261001/trigger-pause-before-review.json`。同一 AGY 会话先返修首台，未接受前不推广、不恢复定时触发。
- 飞书身份：bf2025、436 各自已有且不同，其余 6 台尚缺自己的绑定。版本/CLI/cron 与飞书投递分别验收，不复制其他机器身份，不回退 Telegram，不外发正常诊断消息。
- B1 的限定真实指标任务已独立接受：CMB-2、run `7c1712b6-7609-4ad4-9419-2d1a717b7751`、独立产物完整文件 SHA256 `ddb0247136137d03a5846704765e82c55a7fcd96da14d2b1a5e4fb26ea39c8d2` 及回执正文吻合，指标与后续实际主机读数吻合。原生 comment.runId 为空，不能将正文中的 run 关联误写成原生字段绑定。
- B1 的 59 项相关测试通过仍不足以接受周期任务；独立负向复现发现所有权读取失败放行、当前 run 多 issue 选错、近期旧产物、启动异常与 comment 失败遗留状态、嵌套独立 session 模型进程未清理、原始错误输出上传等边界。已交唯一代码 worker 收口，由主 Codex 复核后才部署定时接法。
- 程序/headless 基础可复制，真实 AGY 同一会话进入 B2：准备其他 6 台独立程序、公司/context/服务，meiren/qiaobird 等无有效 CM cron 的主机可先迁默认 CLI；greenrise/colocrossing/moonrise 保留旧唯一时钟，候选 native schedule 不启用。bf14仍暂停。
- 最后薄适配已由根审查：107 项适配测试及 12 项参数化子测试通过。执行器严格绑定 run/issue/routine，按本轮 artifact 判断；超时/中断清理自有子树，API 回写失败不会假成功。旧一次性执行库保留，不启动旧调度器。
- BF 的修正版真实任务 CMB-5 已接受：run `0da6f774-56ee-4cb6-9e2b-cf0ddef72394` succeeded/exit0，issue done，contextSnapshot.issueId 对应，独立指标产物完整 SHA256 `7417c5921b1976b8a5a5cde3ee2018f284610bfd436ffaad8d2346ef2e9c881d` 与回执一致，原 5 条 root cron 哈希不变。周期触发恢复仍以映射及 watchdog 实测为前提。
- 原生 routine 变量不能只写 definitions：上游会删除未在 title/description 中引用的变量。迁移使用 description 中 `{{cmJobId}}` 引用并回读，运行时再按变量与 originId 绑定，避免 CLI exit0 但映射未保留。
- 原生源码复核纠正了“blocked 会永久挡住下轮”的假设：只有关联 live heartbeat 的 issue 被视作正在执行，terminal run 释放归属。保留 skip_if_active，不为此改变业务入队策略。两个 RSS/weekly 任务按实际产物归为 business always；Moon weekly 原 07:20 与 quiet 至 08:00 冲突留为原有时间边界，不算已真实产出。
- BF 的 14 个原 schedule 已恢复，旧 system/user daemon 都 MainPID0。真实只读 cron CMB-7 经原 Claude/sonnet 执行后 done，native run `808660d8-ddbf-42e4-b221-61c2f1db5ea5` succeeded/exit0，本轮独立产物完整 SHA256 `ba1ce2fd311f3e0efbfbf72d6cc7e698dd8563584b4cfb5c47595464feff38c0`，written_at 在本轮窗口，正文 4616 字符；正常不外发。接受执行闭环，不将它扩大为完整风险判读/异常通知/全63项业务验收。
- 真实 AGY B2 因本机 Individual quota 429 退出（未交完整结果），不是六台认证失败。根接续现有 CLI 收口，按 meiren/qiaobird、greenrise/legacy、colocrossing/Moonrise 分配互不重叠的服务器写入 owner；仅私有报告交根，不并行写共享计划/知识、不复制账号。已安装 active 程序复用，不因报告未完成重新下载。
- 最终接管接受：8 台默认 cm/controlmesh 绑定各自已验证 context/company；63 个 schedule（BF14、green12、colo16、Moon21）原时刻/时区、skip_if_active/skip_missed 与静默/业务产物策略回读通过。其余零有效 cron 主机不造空 native_clock 或无用 watchdog。
- 六台各一件真实无模型指标任务均 done/succeeded/exit0，本轮独立文件完整 hash、执行窗口及 comment.createdByRunId 匹配；根直接回读未重复模型调用。Colo 三件存量工作自然结束，未杀在进行中任务。Moon/legacy 的新服务曾漏开机启动，根发现后 enable 并回读，MainPID 不变、未 restart；新服务全部持久启动，旧消费者 MainPID0。

执行者：真实 AGY CLI 已实施主要程序部署，额度退出后由根协调现有 CLI 工作继续收口；最终审批/文档整合：根 Codex。派发后不持续调用协调模型盯进度；结果或异常到达后继续判断。协作仅用于本轮实施/核对，不增加运行服务。
