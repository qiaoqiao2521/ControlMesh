# ControlMesh

CM 采用轻量 Agent 调度方式：默认使用 **MCode 原生后台任务完成通知**，跨 Agent 消息协作选用 [hcom](https://github.com/aannoo/hcom)。各 CLI 保留已有登录、模型配置和原生会话，由发起会话中的协调 Agent 派发并独立验收结果。

MCode → AGY → 原 MCode 会话的单次空闲接续已实测通过；hcom 已选定，尚未安装或本机验收。当前方向与使用边界见 [PROJECT.md](PROJECT.md)、[最新决策](docs/DECISIONS.md#2026-10-18--默认采用-mcode-后台完成通知与-hcom)和[调度进度](plans/codex-callback-bridge/progress.md)。

已有 [Paperclip 部署](plans/paperclip-based-cm/progress.md)保持原运行所有权；本次方向记录不执行迁移或停用。
关键决策可按需启用[会审 v1](docs/decision-consultation-v1.md)：独立意见、有限补充、证据与分歧，不强制每个任务多 Agent 化。
436 的新命令、飞书入口与恢复方式见 [Paperclip CM 运行说明](docs/paperclip-436.md)；[真实收发复测状态](plans/436-paperclip-feishu/progress.md)单独记录。
Codex App 接收端保留 [codex_callback 薄适配](docs/codex-callback.md)与 native queue，独立入口为 `cm-codex-callback`。
以下功能和安装命令描述保留的旧 Python CM，**不代表 Paperclip 集成安装或生产迁移已完成**。

## What

ControlMesh lets you:

- work interactively in an enhanced local terminal;
- run the legacy bot runtime through Feishu, Telegram, WeChat, Matrix, and compatible
  transports;
- create persistent background tasks that can ask for input, resume, recover, and deliver
  results;
- coordinate bounded multi-agent topologies on a shared Python runtime;
- inspect tasks, providers, events, topologies, and artifacts through a local read-only Web
  dashboard.

Python remains authoritative for the preserved legacy production paths. The TypeScript workspace provides public protocol
models, runtime validation, an SDK, and the local dashboard.

## Quick Start

Install the released CLI:

```bash
pipx install controlmesh
controlmesh
```

`controlmesh` opens the enhanced terminal. Use `/cm` for provider-native mode and `/back`
to return. Source installs also provide `cm` as a shell-command alias for `controlmesh`
(including `cm --help` and `cm --version`); older releases may only provide `controlmesh`.
Start the legacy messaging runtime with:

```bash
controlmesh bot
```

Develop from source:

```bash
git clone https://github.com/qiaoqiao2521/ControlMesh.git
cd ControlMesh
uv sync --locked --all-extras --dev
uv run controlmesh
```

Verify the toolchain:

```bash
python scripts/doctor_toolchain.py --strict --require-bun
```

Evaluate the read-only Alpha from an isolated install:

```bash
pipx install --suffix=-alpha "controlmesh[api]==0.42.0a1"
controlmesh-alpha api serve
```

Open the printed local dashboard URL and enter the printed bearer token. The Alpha server
binds only to `127.0.0.1` and exposes read-only `/api/v1` routes; see the
[read-only Alpha guide](docs/read-only-alpha.md) for the complete five-minute flow.

## Documentation

- [Project Context](PROJECT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Decisions](docs/DECISIONS.md)
- [Installation](docs/installation.md)
- [Read-only Alpha](docs/read-only-alpha.md)
- [Feishu Setup](docs/feishu-setup.md)
- [Telegram Setup](docs/telegram-setup.md)
- [WeChat Setup](docs/weixin-setup.md)
- [Enhanced Terminal](docs/terminal.md)
- [Full Documentation Index](docs/README.md)

Contributors and coding agents should begin with [AGENTS.md](AGENTS.md).

## Status

The Python terminal, bot, task, provider, memory, transport, and multi-agent runtime is the
stable core. The authenticated `/api/v1` facade, TypeScript SDK, and local Web dashboard are
an additive read-only product layer. TypeScript task mutation and runtime replacement remain
blocked until Python golden parity and rollback gates exist.

## License

MIT. See [LICENSE](LICENSE).

## Workflow integration (v0.43.0)

See [implementation boundaries and commands](docs/CODEKIT-INTEGRATION.md).
