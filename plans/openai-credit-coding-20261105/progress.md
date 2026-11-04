# Progress

## Current
已完成用户纠正：原 ~/.dsh 的日常 web 已接入 OpenAI；Magpie 仅反代 ZCode/MCode。三路均在日常 3080 网页实测返回，原有会话保留。旧独立入口仅保留历史材料，服务已停止。

## Done
- 核实已安装工具版本和官方 adapter 存在。
- 读取当前 CM/CapMesh 轻量 CLI 约定。
- 专用受限 API Key 已创建并保存到用户私有配置目录。
- 官方 Responses route、GPT-6.1 Sol/high 已生效；最初独立 Home 入口已被日常接入取代。
- DSH 读取文件、复现失败、实际修改、运行测试；5 项测试全部通过，主 Agent 重跑通过。
- 原 ~/.dsh 的 web/headless/tui 已接入 direct OpenAI；启动器改为复用原 Home，仅用临时 overlay 选择模型。
- 已停止本轮 3082 实例，原生日常网页使用 3080，原有会话仍可见。
- 日常 3080 页面已实际返回 daily-openai-ok，随后已恢复原默认 ZCode。
- Magpie 原生 systemd 服务已恢复，仅监听本机 3425，不启动 3430 Web 管理界面。
- Qoder/WorkBuddy 插件已停用；非目标原生 provider 停用；DSH 网关 Key 限定两路。
- ZCode 通过原生 app-sign-in 关联既有本机账号；真实请求返回 200/end_turn/zcode-proxy-ok。
- 日常 DSH 同一网页进一步实际返回 daily-zcode-ok，8 秒完成，无工具调用。
- 用户已手动完成 MCode 设备授权；浏览器显示“授权已确认”，同一原生登录进程正常结束。
- 原生 catalog 仅两路七项，DSH 原生同步保留 OpenAI 并更新旧型号。
- 日常 DSH 已实际返回 daily-mcode-ok，4 秒完成，无工具调用；默认模型再次恢复 ZCode。
- bash-n、原生 dump-config 与 overlay 合成检查通过；3080/3425 正常，3082/3430 未监听。

## Remaining
- 无功能待办。专用 API 赠送额度的具体扣减刷新仍以账单为准。

## Issues
- API 已调用成功；账单尚未显示赠送额度扣减更新，保留该限制，不重复调用消耗额度。
- 排查时曾发现日常 DSH 默认 Magpie/ZCode，但 Magpie 服务 inactive/disabled、3425 未监听，现已恢复；原 shell 的 systemctl 错误来自缺少 DBUS/XDG 环境。
- 初始 Magpie plugin-auth.json 不存在；不能把历史 signedIn 缓存当作当前关联。ZCode 可复用 app 登录，MCode 插件要求独立设备 OAuth，不读取或替换 mcode 原有 auth。
- 全局 discovery off 会停用订阅插件认证。已恢复必要原生 discovery，使用 provider off、插件开关和调用 Key allowlist 收敛范围。批量 builtin off 已回滚到原生基线，仅禁用 warmups。
- 既有 Orca 候选遗留变更及 experiments/work 未整合。旧计划已标为历史且有未完成真实验收，不能在本任务中重新发布。保留 owner 为根 Codex，最短入口为 plans/cm-orca-headless-bridge-v0/progress.md；当前任务仅提交自己的计划与配置入口。

## Next
日常命令保持 dsh web；dsh-openai 仅为命令行选用官方 API 的辅助入口。

## Cleanup
已移除重复 run.jsonl、空 stderr、可重建 pyc 和临时配置/审阅图片。已停止独立 3082 服务，并删除本轮五个登录临时日志/交接文件，共释放 852 字节（这些文件从 852 字节降为 0；未重写其他工作区）。保留原生 DSH 会话、当前 demo、功能预览和日常网页的私有启动输出。已关闭完成授权的临时浏览器页。

保留原生私有配置备份：~/.dsh/config-backups/daily-openai-magpie-20261105 与 ~/.config/magpie/backups/gateway-only-20261105-040127。回滚时先停对应原生服务，再按备份原文件名恢复配置；不覆盖现有凭据或会话。未删除原 ~/.dsh 内容。

## Knowledge
no_reusable_delta：沿用现有 CM D030 与原生 DSH 配置；本次账户与额度状态保留在本计划。

## Follow-up: unexpected AGY sign-in and responsiveness
- 用户反馈未经手动登录却出现 AGY Google OAuth。Magpie 非目标 provider 仍 off；相关时段无登录事件，AGY 原生同步未改用户设置。同期信息处理 timer 固定调用纯 OpenCode/MiniMax，没有 AGY 调用证据，保持其正常运行。
- 另一个 Codex 聊天的原生事件确认：04:28:15.284–04:29:35.383 执行 agent_quota_check.py --pick，Qoder ready 后仍启动 AGY，最后 AGY timeout。用户链接中的时间值为 04:28:46.430，位于该区间。时间及触发机制高度吻合；缺少浏览器启动的直接父进程证据，不作为绝对归属结论。
- 最小修复：--pick 首个 ready 后停止，不再为了选择 Qoder 而额外启动 AGY；所有探测关闭 stdin 并新建进程会话，避免继承交互终端。Qoder 不可用时仍保留 AGY fallback；checks 仅含实际已探测项。
- 官方 headless 文档要求缓存认证及无终端环境：https://antigravity.google/docs/cli/headless/ 。本轮没有发起新的真实 AGY 登录/模型请求；终端隔离不宣称为所有认证状态下的浏览器阻断保证。
- 局部 12 项 unittest 全部通过，覆盖首选可用不启动 AGY、首选失败仍检查 fallback；独立只读审阅通过。
- 卡顿采样：Magpie/Bun RSS 合计约 126 MiB、合计约 1% 单核 CPU、无自身 swap；服务组约 554 MiB，其中约 474 MiB 为文件缓存。历史服务组内存峰值约 2.13 GiB，发生时间未确定。当前全机可用约 9.1 GiB，CPU 空闲 73–83%，IO wait 0%，短时存在少量换页；不能据此判定用户卡顿瞬间的原因。未停止其他进程或清空 swap。
- 本次只修改既有探测脚本、相关回归测试和本进度。无新增 daemon、登录状态或临时产物需要清理；属于局部修复，沿用现有知识约定。
