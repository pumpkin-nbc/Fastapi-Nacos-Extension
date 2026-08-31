# 兼容性

支持范围为 Python `>=3.8`、FastAPI `>=0.112.2,<0.125.0`、`nacos-sdk-python>=2.0.0,<3.0.0`。CI 交叉验证 FastAPI 0.112.2/0.124.4 与 SDK 2.0.0/2.0.11，集成环境固定 Nacos 服务端 2.3.2。

0.1.0 仅使用经典同步 `nacos.NacosClient` API，并通过 Starlette 线程池移出事件循环。Python 3.8 是语法和类型基线，wheel 包含 `py.typed`。

