# 开发入口

先读 [AGENTS.md](../AGENTS.md)、[PROJECT.md](../PROJECT.md) 和当前任务记录；按行为只读相关实现。

| 行为 | 实现 | 验证 |
| --- | --- | --- |
| 执行与验收报告 | `controlmesh/execution.py` | `tests/execution/` |
| SpecMesh 材料接口 | `controlmesh/workflow.py` | `tests/workflow/` |
| 跨仓状态引用 | `controlmesh/closeout.py` | `tests/test_closeout.py` |
| 可选通知竞态 | `vendor/codex_callback/` | `tests/callback/` 与上游测试 |
| 可选陪伴记忆 | `plugins/dsh-companion-memory/` | 插件自身测试 |

核心入口无需加载第三方运行时：

```sh
python3 -B -S -m controlmesh --help
python3 -B -S -m unittest discover -s tests/execution -v
python3 -B -S -m unittest discover -s tests/workflow -v
```

SpecMesh 真实接口测试需要显式设置 `CM_SPECMESH_TEST_ROOT` 为独立 checkout；未配置时该集成类跳过，不能说已验通。配置错误须报告失败，不能把它当作无依赖而跳过。

`cm-closeout` 的测试使用 pytest，见 [用法与验证](closeout.md)。可选通知测试命令和来源见 [UPSTREAM.md](../vendor/codex_callback/UPSTREAM.md)，DSH 测试见 [插件说明](../plugins/dsh-companion-memory/README.md)。这些定向检查不需要真实厂商调用、凭据或运行服务。

本地验证结果、跳过原因和未覆盖项写入原任务的进度。需要调用真实 CLI、测试通知或部署时单独核验本轮条件，不能把 mock、进程退出或本地文件结果扩大成全路径成功。

旧平台源代码已从工作树移除；只在调查历史时读取 [851d78b](https://github.com/qiaoqiao2521/ControlMesh/tree/851d78b8989d07281d0082a5105f878a99f589c8)。不恢复旧迁移测试矩阵作为新功能的默认门槛。
