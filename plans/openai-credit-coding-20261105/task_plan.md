# OpenAI API 额度编程工具配置

## Goal
使用已领取的 OpenAI Platform 赠送额度，配置可直接编辑项目并运行测试的现有编程工具。

## Latest user correction
2026-11-05：用户要求接入日常 `dsh web`，不是独立 Home/3082 实例。Magpie 仅负责 ZCode、MCode 反代，其他路由及附加管理功能退出本次活跃入口；保留已有账号和会话。

## Scope
- 优先复用本机 DSH；OpenCode 作为现成候选。
- 使用官方 API 地址和普通 API 模型，保留既有登录、代理、模型和会话。
- 不启用自动充值，不接入新的调度或跨 Harness 平台。
- 在独立小项目验证读文件、修改文件、运行测试，并核对 API 计费归属。

## Phases
1. [complete] 核实官方接入与本机配置。
2. [complete] 配置独立 API 入口和凭据引用。
3. [complete] 真实编码和测试通过；账单扣减尚未显示，保留证据边界。
4. [complete] 独立入口已验证；已被最新日常接入要求取代。
5. [complete] 在原 ~/.dsh 接入官方 OpenAI；Magpie 收敛为 ZCode/MCode；日常 web 三路真实回复均通过，默认恢复 ZCode。

## Success
用户可从项目目录启动工具；模型通过官方 API 完成文件修改和测试；交付中明确真实验证及计费证据边界。
