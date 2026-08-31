# FastAPI-Nacos-Extension

[English](README.md) · [中文文档](docs/quickstart.zh-CN.md) · [更新日志](CHANGELOG.zh-CN.md)

`fastapi-nacos-extension` 0.1.0 是面向生产环境的 FastAPI / Nacos 2.x 类型化插件，提供服务注册与注销、服务发现、配置中心原文读取、本地健康状态、有界优雅关闭以及 fork 后恢复。所有同步 Nacos SDK 调用均在线程池中执行，不阻塞 ASGI 事件循环。

> PyPI 发行名为 `fastapi-nacos-extension`，Python 导入名为
> `fastapi_nacos_extension`。本项目与公共 PyPI 上已有的
> `fastapi-nacos` 项目无关。

## 兼容范围

- Python 3.8 及以上
- FastAPI `>=0.112.2,<0.140.0`；Python 3.8 自动解析到最高兼容版 0.124.4
- `nacos-sdk-python>=2.0.0,<3.0.0`，验证 2.0.0 与 2.0.11
- Nacos 服务端 2.3.2，与参照 Flask-Nacos 项目保持一致

CI 还会在对应的 Python 版本上验证 FastAPI 0.125.0 及以上版本，当前覆盖到
0.139.2；完整组合见兼容性文档。

## 安装

首次发布到 PyPI 后可执行：

```bash
python -m pip install fastapi-nacos-extension
```

也可以安装 GitHub Release wheel：

```bash
python -m pip install ./fastapi_nacos_extension-0.1.0-py3-none-any.whl
```

或在源码目录执行 `python -m pip install .`。

## 快速开始

```python
from fastapi import FastAPI
from fastapi_nacos_extension import FastAPINacos

app = FastAPI()
nacos = FastAPINacos(
    app,
    {
        "NACOS_SERVER_ADDR": "127.0.0.1:8848",
        "NACOS_SERVICE_NAME": "orders-api",
        "NACOS_SERVICE_IP": "127.0.0.1",
        "NACOS_SERVICE_PORT": 8000,
        "NACOS_AUTO_REGISTER": True,
        "NACOS_HEALTH_CHECK_ENABLED": True,
    },
)


@app.get("/upstream")
async def upstream():
    return await nacos.get_one_healthy_instance(app, "payments-api", strategy="weight")
```

初始化阶段只校验本地配置、保存状态和注册路由；Client 创建与网络访问会延迟到应用启动或首次显式异步调用。

## 关键约定

- 配置优先级：内置默认值、构造器配置、`init_app()` 应用配置。
- 所有应用相关 API 都必须显式传入 `app`，不模拟 Flask 隐式上下文。
- 状态位于 `app.state.nacos`；同一扩展重复初始化幂等，其他对象占用时明确报错。
- 自动注册在 lifespan 启动时触发且不等待网络收敛；关闭时按配置执行有界注销。
- 每应用、每 PID 最多一个生命周期 Worker 和一个 Naming RPC。
- “最后命令优先”，已注册的准确身份会缓存并用于注销。
- 支持 Uvicorn/Gunicorn 多 Worker、preload/fork 后 Runtime 重建。
- 配置中心只返回原始文本，不解析、不监听、不写回应用状态。
- `get_status()` 固定返回 16 个本地字段；可选健康路由固定返回 7 个字段。
- 原始 Nacos SDK 日志默认隔离，避免凭证或配置内容泄漏。

## 文档

- [快速开始](docs/quickstart.zh-CN.md)
- [配置参考](docs/configuration.zh-CN.md)
- [API](docs/api-reference.zh-CN.md)
- [服务注册](docs/service-registration.zh-CN.md)
- [服务发现](docs/service-discovery.zh-CN.md)
- [配置中心](docs/config-center.zh-CN.md)
- [健康检查](docs/health-check.zh-CN.md)
- [生产部署](docs/production.zh-CN.md)
- [故障排查](docs/troubleshooting.zh-CN.md)
- [兼容性](docs/compatibility.zh-CN.md)
- [发布流程](docs/release.zh-CN.md)

## 许可证与来源

本仓库使用 GPLv3。代码从 Apache-2.0 的 Flask-Nacos 项目适配而来，详情见 [NOTICE](NOTICE)。
