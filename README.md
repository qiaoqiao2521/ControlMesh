# ControlMesh

CM 是工作流概念与薄适配层，实际运行底座是 [Paperclip](https://github.com/paperclipai/paperclip)，不是另一个独立运行时。
复用上游的任务生命周期、派发与事件唤醒，只补必要的 CLI/TUI、消息入口、策略与交付适配，不重建调度器。

当前方向与验收边界见 [PROJECT.md](PROJECT.md) 和 [Paperclip 计划进度](plans/paperclip-based-cm/progress.md)。
436 的新命令、飞书入口与恢复方式见 [Paperclip CM 运行说明](docs/paperclip-436.md)；[真实收发复测状态](plans/436-paperclip-feishu/progress.md)单独记录。
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
git clone https://github.com/muqiao215/ControlMesh.git
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
