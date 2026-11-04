# DSH · OpenAI API 编程入口

已复用本机 DSH 0.2.1-rc.2，使用普通 API 模型 `gpt-6.1-sol`，推理级别 high。
官方地址为 `https://api.openai.com/v1`，协议为 `openai-responses`。

## 在项目里运行

```bash
cd /你的项目目录
dsh-openai "修复指定问题，并运行相关测试"
```

需要事件流时：

```bash
dsh-openai --json "读取当前项目，完成修改并运行测试"
```

网页入口已在本机 `http://127.0.0.1:3082/` 启动，并在日常 Chrome 中完成本机登录。
可用“添加工作区”选择实际项目。当前展示的是独立验证项目。
服务未运行时，从目标项目目录启动原生网页应用：

```bash
dsh-openai web --host 127.0.0.1 --port 3082
```

原生启动输出会提供本机登录 URL。该 URL 含临时登录凭据，不写入仓库或共享。

## 配置位置

- 启动器：`~/.local/bin/dsh-openai`，链接到本目录的 [dsh-openai](dsh-openai)。
- 原生配置模板：[cordis.patch.yml](cordis.patch.yml)。
- 已安装配置：`~/.local/share/dsh-openai-credits/cordis.patch.yml`。
- 私有 API Key：`~/.config/dsh-openai-credits/api-key`，权限 600；无密钥值入库。
- DSH 数据、原生会话、演示项目：`~/.local/share/dsh-openai-credits/`。
- 使用独立 DSH_HOME；现有 `~/.dsh`、OpenCode 和其他账号配置保留。
- 关闭原生 telemetry：`DSH_TELEMETRY_MODE=DISABLED`。

需要选用另一个已配置模型时，在原生模型菜单选择 `gpt-6-astra`，或编辑 agent-default-model。

## 实测

2026-11-05，官方 `GET /v1/models` 返回 200，确认所选模型可用。
真实 DSH 任务调用 `read`、`edit`、`bash`；先发现折扣计算失败，再修改 `invoice.py` 并运行 unittest。
5 个测试全部通过，主 Agent 独立重跑通过；测试文件保持原样。
网页已读取同一原生会话，可查看修复结果和轨迹。

赠送额度覆盖普通 Responses 调用，是否扣减以 API 组织账单为准。
本轮检查时尚未看到扣减更新；不把调用成功等同于账单已刷新。具体账户金额仅留在本机验证记录。
未添加付款方式或开启自动充值。

## 来源

- [DSH 官方多模型 adapter](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/llm/llm-pi-ai)
- [OpenAI 订阅赠送 API 额度范围](https://developers.openai.com/api/docs/guides/chatgpt-api-credits)
