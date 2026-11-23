# 安装与运行

核心工具需要 Python 3.11+；`cm run` 当前仅支持 Linux，其他系统会在执行命令前拒绝。`cm-closeout` 和 SpecMesh 的 Git 核验另需 Git。核心执行不要求模型账户或运行后台服务。

## 从当前源码安装

```sh
git clone https://github.com/qiaoqiao2521/ControlMesh.git
cd ControlMesh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
cm --help
```

本仓库当前目标版本为 0.44.0；推送源码不代表已上传 PyPI。安装旧发布版本不会得到本轮删减和新入口。

## 不安装包

从 checkout 根目录直接使用标准库入口：

```sh
python3 -S -m controlmesh --help
python3 -S -m controlmesh run --help
python3 -S -m controlmesh.workflow --help
python3 -S -m controlmesh.closeout --help
```

实际执行需要提供明确命令、一个新报告路径以及检查要求，见 [cm run](run.md)。CLI 和模型按各自现有方式配置；CM 不替它们建立账户、选择模型或跳过权限。

## 可选组件

- 跨会话材料核验使用显式指定的独立 SpecMesh checkout，见 [交接](workflows/small-change.md)。
- 外部 CLI 可复用已配置的 agent-link，见 [选择规则](agent-link-subagents.md)。
- `vendor/codex_callback` 只随源码保留，未默认打包。真实通知还依赖可达的原 Codex 线程和控制通道，见 [callback](codex-callback.md)。
- DSH 陪伴记忆按 [插件说明](../plugins/dsh-companion-memory/README.md) 独立安装。

旧配置、登录态、任务数据和服务器不由此安装流程迁移。已有旧版本用户在独立 checkout / 环境验证当前入口后，再按自己明确的部署任务处理服务。
