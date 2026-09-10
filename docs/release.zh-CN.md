# 发布流程

公共发行名为 `fastapi-nacos-extension`，与 PyPI 上无关的 `fastapi-nacos` 项目相互独立。只有在以下条件全部通过时才允许创建 `v0.1.0`：版本一致性、Ruff、mypy、完整 pytest、分支覆盖率至少 85%、Python 3.8 基线及分版本 FastAPI/SDK 兼容矩阵、wheel/sdist 构建、Twine 元数据、包内容及安装冒烟。

## 首次配置 Trusted Publisher

在 GitHub 仓库中创建 `pypi` Environment，并在 PyPI 配置 Trusted Publisher；
如果项目尚未创建，则配置同名的 Pending Publisher：

- Owner：`pumpkin-nbc`
- Repository：`Fastapi-Nacos-Extension`
- Workflow：`release.yml`
- Environment：`pypi`
- PyPI Project Name：`fastapi-nacos-extension`（仅 Pending Publisher 需要）

GitHub 中不保存 PyPI API Token。只有独立的 PyPI 发布任务获得 `id-token: write` 权限，构建与验证任务保持只读。工作流不提供手动触发入口。

## 正式发布

将发布提交合并到 `master`，创建与项目版本完全一致的标签（例如 `v0.1.0`）并推送。工作流会自动确认标签提交属于 `master`、标签与声明版本一致且 PyPI 尚无同版本，然后通过 Trusted Publishing 发布。只有 PyPI 发布成功后，才会使用同一份 wheel 和 sdist 创建 GitHub Release。
