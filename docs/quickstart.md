# Quick start

Install a 0.1.0 wheel and create the application shown in the root README. A
factory can keep one extension instance and initialize multiple applications:

```python
from fastapi import FastAPI
from fastapi_nacos import FastAPINacos

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

The constructor's first positional argument is `app`; pass shared settings with
`config=`. Start a disposable Nacos 2.3.2 instance with
`examples/docker-compose-nacos.yml` for manual testing.
