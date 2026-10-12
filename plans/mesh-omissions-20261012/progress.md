# Progress

## Current
2026-10-12：本轮确认的遗漏已修复交付。CapMesh 常用 main 入口恢复，旧现场完整保留；两条当前状态引用同步一致。QIA-100 研究修订接受，原生 done 读回；本机启动/恢复入口已安装并验证。CM 与 CapMesh 已提交推送，远端 main SHA 独立读回一致。

## Done
核对隔离 GitHub 身份 qiaoqiao2521 / 238822818；CapMesh 为其既有私有仓库。
- 原主目录移至 /home/muqiao/projects/CapMesh-legacy-20261012，162 个文件内容/权限、HEAD、分支与 git status 完全一致；所有既存 linked worktree 修复连接。
- 复用干净的既有发布 worktree 移至常用路径，切 main 并 fast-forward 至已获取远端9064cf9，无新增仓库或丢弃变动。
- closeout 本机目标改为常用路径，另声明 callback Current 的独立同步关系；原配置私有备份已保存。
- 当前总览归纳飞书持续对话、callback 与治理来源；修正架构页仍称完成钩子未接通的过时说明。同步一致不证明来源新鲜，接收关系必须显式维护。
- 新 cm-codex-task launch/reconcile 复用 bind、native-watch、原生 API 和 notify；私有 attempt 在派发前独占落盘，未知响应不重发。入口已安装，symlink help 实测通过。
- QIA-100 五项内容修订按官方 Linux/build/server/FAQ/context 复审接受；修订 report/research/acceptance 私有保存，原四份产物与 handoff 哈希不变。原生 in_review → done 读回；接受范围仅资料研究，一次性 Agent 仍 paused。
- 使用原 QIA-100 run 实测 reconcile：replayed=true，前后完整 callback status 一致；原 handoff 未改写，无新 callback、任务重派发或模型重跑。
- 31 项 Node 启动顺序、误归属、未就绪、绑定拒绝、未知派发、篡改与恢复测试通过；51 项 Python（36 callback、15 closeout）通过。两入口 Node 语法与已安装 help 通过。
- 来源修复提交 bd4e6d0b0039f638db712c75e65dd600159b1ece 已推送到既有公开 ControlMesh main；CapMesh 修复提交 1773cf181d14049d3308d5e2444c625cbc7fba58 已推送到既有私有 CapMesh main。隔离账号与两个远端 main 通过 GitHub API 读回一致。最终进度修订同批交付，以本文件 Git 历史为准。
- cm-closeout 首次 check 显示两项待同步；sync 更新两项，后续 check=已一致。CM 116 个与 CapMesh 35 个相对文档链接按 Git 跟踪目标检查，暂存 diff 与凭据模式检查通过；未提交运行数据。
- 最终再次核对 legacy 的 162 文件哈希/权限、原 HEAD/分支与相同模式的 git status 一致。CapMesh main 工作区干净；CM 只保留下方已登记遗留。

## Remaining
本轮遗漏修复没有未完成步骤。新 launch 完整真实派发、长期后台服务及普通 App 重启仍待对应授权任务验收；owner 根 Codex，入口 docs/codex-callback.md。它们没有被这次隔离测试或原运行对账冒充通过。

## Issues
## Retained work and handover

根 Codex 串行收尾；以下保留项没有被丢弃或混入已接受提交。

- Orca 桥/CLI/探针/测试与 cron 提案：实际 diff 和原 owner/阻碍已复核。默认方向被 Paperclip 取代，A01–A12 与独立审批仍未全接受。最短入口是 plans/repository-closeout-policy/progress.md 的 Handover，随后对应测试与原提案审查。
- 旧 436 bootstrap 与 work/cm-436-migration-20261001：保留历史归属；脚本与当前 agent436 system unit 不符，不作为当前部署入口。最短入口是 plans/436-paperclip-feishu/progress.md。
- Tau-bench：原实验已在 codex/tau-bench-20261001 发布，不能把本地副本再当未发布新实现或恢复生产队列。保留私有运行 output 与 .runtime；先核对 plans/tau-bench-20261001/progress.md 和已发布分支，再决定合入范围。owner 根 Codex。
- Sandpile：原计划记录作品、QA、附件与 native done；本轮未重做浏览器 QA 或核对二进制包/公开许可，不能直接批量入库。保留 experiments/sandpile-qia73 与 plans/free-time-sandpile-qia73；最短入口为其 progress 和 README。owner 根 Codex。
- work/feishu-matrix-20261012：本轮观察到当日仍更新的 host-snapshots / moon-credential-rebind / moon-listener-diagnostic；可能正在执行且包含运行与凭据边界材料。本轮不读取或发布原数据，不触碰正在进行的变动。接续 owner 原任务主 Agent 与根 Codex，先核对原任务状态再串行归档。
- CapMesh legacy：原 162 文件、状态与分支保留；其 Git common directory 仍为当前 worktree 所依赖。旧审查结论先从 reviews/capmesh-legacy-review-20261001.md、reviews/skill-project-legacy-handoff-20261001.md 核对，未接受实验不批量发布。owner 根 Codex。
- 自媒体仓库现有内容/游戏/Night Lab 变动保持原归属；该仓库没有既有 Git remote。QIA-100 修订放原忽略目录，不把运行日志或会话状态加入 Git。后续内容交付先读对应 task plan，不能为此次修订擅自新建远端。

## Next
下一次明确绑定的本机任务采用已安装 launch；出现未知或断线结果先 reconcile 原 run，再由原会话独立接受业务。无需重派发 QIA-100 或重跑模型来重复本次验收。

## Knowledge closeout
already_covered：实际采用 Wiki/自动化开发范式与智能体协作.md 的分层验收和未知提交先对账；遵循 Wiki/开发协作接入.md 的来源责任。具体新入口和来源覆盖修正维护在 CM 文档与 CapMesh D018，不重复创建共享页。
