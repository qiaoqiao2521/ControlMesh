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
