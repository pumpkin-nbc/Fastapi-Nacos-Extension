# 快速开始

安装 0.1.0 wheel 后可直接使用根目录 README 中的示例。应用工厂模式可复用一个扩展实例：

```python
from fastapi import FastAPI
from fastapi_nacos_extension import FastAPINacos

nacos = FastAPINacos(config={"NACOS_SERVER_ADDR": "127.0.0.1:8848"})


def create_app() -> FastAPI:
    app = FastAPI()
    nacos.init_app(app, {
        "NACOS_SERVICE_NAME": "factory-api",
        "NACOS_SERVICE_IP": "127.0.0.1",
        "NACOS_SERVICE_PORT": 8000,
    })
    return app
```

构造器第一个位置参数是 `app`，共享配置请使用 `config=`。本地联调可启动 `examples/docker-compose-nacos.yml` 中的一次性 Nacos 2.3.2。
