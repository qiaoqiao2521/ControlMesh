# 开发入口

先读 [AGENTS.md](../AGENTS.md)、[PROJECT.md](../PROJECT.md) 和有关任务记录，再读拥有行为的模块。

| 行为 | 实现 | 检查 |
| --- | --- | --- |
| 锁定的原生 T3 Server/Web | `package.json`、`package-lock.json`、`t3-upstream.json` | `npm run check:t3` |
| T3 透明参数与进程转交 | `controlmesh/t3.py` | `tests/test_t3.py` |
| 独立产物与远端验收 | `controlmesh/verify.py` | `tests/test_verify.py` |
| 安装后的命令 | `controlmesh/__main__.py`、`pyproject.toml` | `tests/test_packaging.py`、`scripts/check_package.py` |
| 兼容外部命令执行 | `controlmesh/execution.py` | `tests/execution/` |
| 可选 SpecMesh 交接 | `controlmesh/workflow.py` | `tests/workflow/` |
| 可选跨仓引用同步 | `controlmesh/closeout.py` | `tests/test_closeout.py` |

按改动范围选择检查，沿用 CI 的固定依赖：

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run check:t3
uv sync --frozen --extra dev
uv run --frozen ruff check .
uv run --frozen pytest -q tests
uv build
python3 scripts/check_package.py
```

T3 smoke 使用独立测试状态，验证真实运行时启动，不调用付费模型；首次运行可能下载官方二进制。标准库路径可用 `python3 -B -S -m unittest tests.test_t3 tests.test_verify tests.test_packaging -v` 检查。依赖安装不改变用户的模型或登录配置。

SpecMesh 接口测试需要 `CM_SPECMESH_TEST_ROOT` 指向明确的独立 checkout；未配置的跳过不能称为真实接口验通。当前 CI 固定该独立来源，普通任务不必为无关模块重复检查。

记忆源码、测试和宿主插件由 [AgentTraceMesh](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md) 独立维护；CM 不保留记忆测试任务、`context` 代理、注入参数或回执转发。需要修改记忆行为时，直接在该仓库的任务范围内处理。

`npm run check:t3`、适配测试和产物验证各有范围，不能据此声称真实模型、飞书或生产服务已迁移。实际结果、跳过和未覆盖项写入 [本轮进度](../plans/t3-primary-20261126/progress.md)。历史源码只按需从 [退役索引](retired-components.md) 读取。
