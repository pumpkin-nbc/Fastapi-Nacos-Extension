# 兼容性

支持范围为 Python `>=3.8`、FastAPI `>=0.112.2,<1.0.0`、`nacos-sdk-python>=2.0.0,<3.0.0`。FastAPI 自身的 `Requires-Python` 元数据会为不同解释器选择最新兼容版本，其中 Python 3.8 最高解析到 FastAPI 0.124.4。

CI 兼容矩阵包括：

- Python 3.8：FastAPI 0.112.2/0.124.4，分别交叉 SDK 2.0.0/2.0.11；
- Python 3.9：FastAPI 0.125.0/0.128.8；
- Python 3.10：FastAPI 0.129.0/0.141.1；
- Python 3.11、3.12、3.13、3.14：FastAPI 0.141.1。

集成环境继续固定 Nacos 服务端 2.3.2。

0.1.0 仅使用经典同步 `nacos.NacosClient` API，并通过 Starlette 线程池移出事件循环。Python 3.8 是语法和类型基线，wheel 包含 `py.typed`。
