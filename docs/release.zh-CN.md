# 发布流程

公共 PyPI 已有无关同名项目，因此禁止上传公共 PyPI。只有在以下条件全部通过时才允许创建 `v0.1.0`：版本一致性、Ruff、mypy、完整 pytest、分支覆盖率至少 85%、Python 3.8 基线及分版本 FastAPI/SDK 兼容矩阵、wheel/sdist 构建、Twine 元数据、包内容及全新环境安装冒烟。

发布工作流只把 wheel 与 sdist 附加到 GitHub Release，不包含 PyPI Token 或上传命令。
