# DSH · OpenAI API 编程入口

已复用本机 DSH 0.2.1-rc.2，配置普通 API 模型 `gpt-6.1-sol` / `gpt-6-astra`。
命令行辅助入口默认选择 `gpt-6.1-sol`，推理级别 high。
官方地址为 `https://api.openai.com/v1`，协议为 `openai-responses`。

## 日常网页入口

继续使用原来的命令和配置目录：

```bash
cd /你的项目目录
dsh web
```

网页地址为 `http://127.0.0.1:3080/`。在模型菜单选择“OpenAI 官方 API”下的模型。
已接入原 `~/.dsh`，原有会话保留。此前的独立 3082 实例已经停止。

原生启动输出会提供本机登录 URL。该 URL 含临时登录凭据，不写入仓库或共享。

## 在命令行里运行

```bash
cd /你的项目目录
dsh-openai "修复指定问题，并运行相关测试"
```

需要事件流时：

```bash
dsh-openai --json "读取当前项目，完成修改并运行测试"
```

## 配置位置

- 启动器：`~/.local/bin/dsh-openai`，链接到本目录的 [dsh-openai](dsh-openai)。
- OpenAI 配置片段：[cordis.patch.yml](cordis.patch.yml)，供参考，已合并到日常配置。
- 日常配置：`~/.dsh/profiles/{web,headless,tui}/cordis.patch.yml`。
- 命令行临时模型选择：`~/.dsh/openai-api.patch.yml`；仅切换默认模型。
- 私有 API Key：`~/.config/dsh-openai-credits/api-key`，权限 600；无密钥值入库。
- 日常 web 通过原生凭据引用 `OPENAI_CREDITS_API_KEY` 读取同一 Key。
- 启动器使用原 `~/.dsh`，并通过环境变量读取 Key；不创建独立 Home。
- 旧独立目录 `~/.local/share/dsh-openai-credits/` 仅保留编码演示及历史验证材料。
- 启动器关闭原生 telemetry：`DSH_TELEMETRY_MODE=DISABLED`。

需要选用另一个已配置模型时，在原生模型菜单选择 `gpt-6-astra`，或编辑 agent-default-model。

## 实测

2026-11-05，官方 `GET /v1/models` 返回 200，确认所选模型可用。
真实 DSH 任务调用 `read`、`edit`、`bash`；先发现折扣计算失败，再修改 `invoice.py` 并运行 unittest。
5 个测试全部通过，主 Agent 独立重跑通过；测试文件保持原样。
随后日常 `3080` 网页选择同一官方模型，实际返回 `daily-openai-ok`；原有会话仍可见。

赠送额度覆盖普通 Responses 调用，是否扣减以 API 组织账单为准。
本轮检查时尚未看到扣减更新；不把调用成功等同于账单已刷新。具体账户金额仅留在本机验证记录。
未添加付款方式或开启自动充值。

## Magpie 范围

Magpie 仅供 DSH 反代 ZCode 和 MCode（`minimax-code`）。
OpenAI 直接访问官方地址，不经过 Magpie。
本机服务监听 `127.0.0.1:3425`，不启动 Magpie Web 管理界面。
Qoder、WorkBuddy 插件停用；其他原生账号保留，非目标 provider 停用。
DSH 使用独立受限网关 Key，仅允许 `zcode/*` 和 `minimax-code/*`。
保留必要原生认证与协议依赖，不另建路由管理平台。

两路原生登录关联已恢复。日常 `3080` 同一网页分别返回 `daily-zcode-ok`（8 秒）和 `daily-mcode-ok`（4 秒），均未调用项目工具。
MCode 本轮实际使用 `minimax-code/MiniMax-M3.1-Flash-Preview`；旧 `MiniMax-M3.1-Flash` 名称已由原生模型同步更新。
默认模型恢复为原 `zcode/GLM-5.3`；需要使用 API 额度时，在同一菜单选择 OpenAI。

已停止独立服务并清理本轮五个临时登录文件（852 字节）。保留私有配置备份、原生会话与验证截图；密钥、认证状态及运行日志未入库。

## 来源

- [DSH 官方多模型 adapter](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/llm/llm-pi-ai)
- [OpenAI 订阅赠送 API 额度范围](https://developers.openai.com/api/docs/guides/chatgpt-api-credits)
