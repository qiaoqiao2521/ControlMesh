# Progress

## Current

2026-10-25：CM 轻量方向已交付。本轮按用户要求补验 AGY、CBC、ZCode CLI、DSH：前三个成功调用为 AGY/ZCode/DSH，随机文件标记与筛选求和均独立通过；CBC 额度耗尽，不能使用空 done 冒充成功。Qoder 保留此前验收。本机配置已修正 AGY 参数并加入 zcode、dsh，无新登录、wrapper 或调度服务；后台 queue 未复测。

## Done

- 四 CLI 本轮验收：AGY 参数修正后通过；ZCode CLI 的只读 plan profile 通过；DSH 原生 headless 通过；CBC 通过一次原生 JSON 诊断确认 429，额度恢复前停止请求。各回执与独立比较结果保存在私有目录，公开文档不含会话 UUID、原始日志或凭据。
- agent-link list_agents 已读取五个自定义 profile；新配置无需重启 App 即可调用。说明记录原生 argv、DSH profile 边界、ZCode 只读范围和 CBC 的空成功问题。全局 AGENTS 仅同步已配置 CLI 名称。
- 最终检查：独立回执比较为 AGY/ZCode/DSH 三项通过、CBC 未通过；官方 buildArgs 读回四组实际 argv，原有 Qoder/CBC 配置保持一致，五个配置命令均可执行。三处新增相对链接解析通过，两仓 diff --check 通过；未提交本机配置、fixture 或原始回执。

- 2026-10-25：通过 App 已加载的 agent-link spawn_agent，委派 Qoder 只读核对能力状态与入口冲突。返回 status=done、能力表和具体文件依据；主 Agent 读回主要来源。审查中的旧 MACPIE 状态已据 CapMesh D029 修正，未盲用子 Agent 结论。
- 用内置子 Agent 只读检查 CapMesh 的重复／过时边界；主 Agent 串行整合 D030、PROJECT、能力表、PIT-002 和社区入口。同步结果、内部协作和外部后台 queue 的职责分开写明。
- 更新 README、AGENTS、PROJECT、架构、决策、文档索引、agent-link 使用说明及原回调计划；保留旧实现与按日期标记的历史验收。旧通用记忆排除默认 Mesh，DSH 插件保持可选，Magpie 退出 Codex 的旧决定回填 CM。
- 两仓 54 个新增本地 Markdown 链接与锚点均能解析到已跟踪文件；git diff --check 通过。主 Agent 读回主要差异，子 Agent 复核当前方向和验收边界；未因文档改动运行软件全套测试。两仓远端所有者与有效登录 qiaoqiao2521 / 238822818 已核实。
- 交付已读回：CM 514ea276、CapMesh ace35f7 均与各自 GitHub main 一致。复用 cm-closeout 同步一项 callback 引用，差异已审阅并纳入 CapMesh 提交，最终 check 返回“已一致”。本条仅记录交付结果，后续收尾记录提交以 Git 历史为准。

以下为 2026-10-24 安装记录；当日 App 工具未加载已由上述实际调用补齐。

- 上游配置与子进程源码核对；本机 AGY/Qoder 帮助核对。
- 保存原有未提交工作边界，未改动其内容。
- 安装 agent-link-mcp@0.5.3，注册 Codex 的 agent-link MCP，配置读回 enabled。
- 使用上游 MCP SDK 枚举六个工具、读取已配置 CLI，再派发一次 Qoder 文件任务。
- 实际结果 status=done，随机标记读回、sum=96 和工具成功三项检查通过。
- 私有运行回执：~/.local/state/agent-link-smoke/20261024-qoder-01/result.json。此文件、测试脚本和 CLI 日志均不入库。
- 新增 docs/agent-link-subagents.md，说明明确调用方式、取消与追问边界、卸载方法和验收范围。
- 两个本地 Markdown 链接均存在；三个配置命令均可执行；Codex TOML 解析与目标服务读回通过。运行回执独立读回，三个行为检查通过。
- 当前工具目录未出现 agent-link，新工具实际加载仍待下一轮确认；不将独立 SDK 调用伪装为 App 原生工具调用。
- 交付目标为既有 qiaoqiao2521/ControlMesh main；有效 GitHub 身份 qiaoqiao2521 / 238822818 已核实。提交与远端状态以 Git 历史读回为准。

## Remaining

- App 工具加载与 Qoder 同步调用已于 2026-10-25 完成，后续只在真实任务中按需使用。
- CBC 真实任务未通过，原生 429 额度已用尽；额度恢复后再验收，owner 根 Codex，最短入口为 docs/agent-link-subagents.md 的当前验收。本轮不购买、换账号或切换模型。
- AGY、ZCode CLI、DSH 的同步文件读取已通过；文件写入、取消、恢复等未在本轮测试，不自动扩展测试矩阵。
- 后台 queue 不在同步 MCP 测试验收范围。需要时先恢复原线程共享控制通道；本次不启动新 daemon。

## Issues

- 2026-10-25 开工遗留与既有交接一致：Orca 接线／探针／测试、未接受 cron 提案、旧 436 bootstrap、experiments、work/、.zcodeignore 和 .gitignore 均保留。旧方向已停止，候选仍缺完整发布审查，运行态不得直接入库。owner 根 Codex；恢复入口为 plans/repository-closeout-policy/progress.md、plans/free-time-sandpile-qia73/progress.md 和 plans/tau-bench-20261001/progress.md；不把总结文档等同全仓清理。
- CapMesh 既存 reviews/local-closeout-2026-10-23.md 属于自动检查器的本地观察记录，含其他项目私有路径和当日运行线索，本次读回其范围后继续本地保留，不混入方向决定。owner 根 Codex；若以后要求发布该报告，先复核来源与公开范围。
- 一次文档补丁因同一路径重复 delete/add 被 apply_patch 拒绝，未应用；已改为直接重写获授权的 README 后分别应用其余更新。

- bcb 命令不存在；已核实 cbc 是 CodeBuddy，并按真实入口配置，不创建别名。
- codex app-server daemon 没有 status 子命令，改用 version；该只读查询确认控制 socket ENOENT。
- 原有 Orca、cron 候选、experiments、work/ 等遗留保持不动。接续 owner 根 Codex；最短入口 plans/repository-closeout-policy/progress.md。

## Next

本轮四 CLI 验证完成，结果为三项通过、一项额度阻断。后续使用已验收入口，CBC 额度恢复后再验；需要独立后台回传时才处理 queue 通道。

## Knowledge closeout

2026-10-25 CLI 验证 no_reusable_delta：空 done 不等于业务成功属于已采用的验收原则。具体参数、额度错误和三个通过结果留在本项目；CapMesh 能力表仅更新到实际状态，不新增选型决策、知识页或记忆系统。

2026-10-25 updated：能力取舍已串行写入并读回 CapMesh D030、PROJECT、capabilities/index.md、PIT-002 与社区入口；D024 标明被细化，D028 补同步 MCP 边界，D029 的 Magpie 退出决定回填 CM。Wiki 原有“按当前任务选择验收依据”继续适用，原则 already_covered，不新建知识页或全局记忆记录。

already_covered：采用 Wiki/自动化开发范式与智能体协作.md 的“按当前任务选择验收依据”和“外界 Agent 协作与原生队列”。本次安装、同步工具调用、App 加载、后台接续分开记账；共享知识已覆盖这一原则，不新增 Wiki 页面或索引。
