# 436 模型入口修复验收

验收时间：2026-10-07 00:15，Asia/Shanghai。

## 结果

CM 436 的现有 `opencode_local` Agent 已恢复真实模型调用。Paperclip 通过 `/usr/local/bin/cm-opencode` 执行独立短任务，返回 `CM436模型验收通过`。实际 OpenCode 进程使用 UID 1000，即 `agent436`。

运行完成后，Agent 已自然回到 `idle`，没有 `queued` 或 `running` 任务。独立验收任务已标记 `done`。

## 原因与最小修复

修复前，Agent 使用 `zai-coding-plan/glm-5.1`，状态为 `error`。现有普通用户 OpenCode 配置的 provider 是 `zhipu-coding-plan`，默认模型是 `zhipu-coding-plan/GLM-5.3-Flash`。`cm-opencode models zhipu-coding-plan` 实际列出 `GLM-5.3` 和 `GLM-5.3-Flash`，没有 `glm-5.1`。

通过官方 Agent PATCH 接口，仅提交以下字段：

```json
{"adapterConfig":{"model":"zhipu-coding-plan/GLM-5.3-Flash"}}
```

官方接口合并同类型适配器配置。回读确认：除 `model` 外，其他适配器字段未变，原有 `env` 保留。未读取或复制凭据，未新增 provider、账号或 Agent。原错误状态通过官方 `clear-error` 接口清除。

## 真实运行证据

| 项目 | 值 |
| --- | --- |
| 服务器 | `racknerd-436b0c0` |
| Agent | `3b6a744d-1da2-46a6-b8fd-7298bbd38882` |
| Company | `5dde8cef-0b64-44a3-a6e3-17774326aaea` |
| 适配器 | `opencode_local` |
| 命令 | `/usr/local/bin/cm-opencode` |
| 工作目录 | `/var/lib/agent436/workspace` |
| 模型 | `zhipu-coding-plan/GLM-5.3-Flash` |
| 独立验收任务 | `ec653457-fe51-4349-aa46-c0efa475cff2` |
| 真实运行 | `9a68025f-9001-4afe-b06f-f75183934e33` |
| 运行状态 | `succeeded` |
| 错误代码 | `null` |
| 口令匹配 | `true` |
| 实际 OpenCode UID | `1000` |
| 最终 Agent 状态 | `idle` |
| 最终活跃运行 | `[]` |

验收调用由 Paperclip 真正的适配器发起，采用 Agent 保存的 `OPENCODE_CONFIG`。没有使用手工拼装的替代环境。该任务没有飞书来源绑定，没有发送飞书消息，没有操作业务仓库，没有改变 cron。

## 私有回退入口

原模型 PATCH 及脱敏配置快照保存在服务器：

`/var/lib/agent436/.local/state/cm-provider-verification/model-before-20261006T161457Z.json`

运行回执保存在同一私有目录：

`/var/lib/agent436/.local/state/cm-provider-verification/receipt-ec653457-fe51-4349-aa46-c0efa475cff2.json`

目录权限为 `0700`，文件权限为 `0600`。文件不入库。回退只需通过官方接口恢复快照中的原 `model`；成功修复后未执行回退。

## 验收边界

本记录确认 436 的模型入口、真实普通用户执行、短文本结果和自然收尾。飞书连续对话、上下文记忆及插件重启恢复由主 Agent 单独验收。单次成功不代表套餐余额或长期可用性。
