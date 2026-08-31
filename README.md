# FastAPI-Nacos

[中文说明](README.zh-CN.md) · [Documentation](docs/quickstart.md) · [Changelog](CHANGELOG.md)

`fastapi-nacos` 0.1.0 is a typed, production-oriented FastAPI integration for
Nacos 2.x. It provides process-safe service registration, discovery, raw
configuration reads, local health status, bounded shutdown deregistration and
post-fork recovery without blocking the ASGI event loop.

> This repository is unrelated to the project of the same name on public
> PyPI. Install it from source, a GitHub Release wheel, or a private index.
> Public PyPI publishing is intentionally not configured.

## Compatibility

- Python 3.8 or newer
- FastAPI 0.112.2 through 0.124.x (`>=0.112.2,<0.125.0`)
- `nacos-sdk-python` 2.0.0 through 2.0.11 (`>=2.0.0,<3.0.0`)
- Nacos server 2.3.2, matching the reference Flask-Nacos project

## Installation

From a release wheel:

```bash
python -m pip install ./fastapi_nacos-0.1.0-py3-none-any.whl
```

From a local checkout:

```bash
python -m pip install .
```

## Quick start

```python
from fastapi import FastAPI
from fastapi_nacos import FastAPINacos

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


@app.get("/remote-config")
async def remote_config():
    return {"content": await nacos.get_config(app, "orders.yaml")}
```

Run it with `uvicorn app:app --host 0.0.0.0 --port 8000`. Initialization is
local and lazy: no Nacos client is constructed and no network request is made
until application startup or the first explicit async operation.

## Public API

All application-scoped operations take an explicit `FastAPI` instance. The
synchronous Nacos SDK is always called from a worker thread.

```python
FastAPINacos(app=None, config=None)
init_app(app, config=None)
await register_instance(app)
await deregister_instance(app)
await get_client(app)
get_cached_client(app)
get_config_snapshot(app)
await list_instances(app, service_name, group=None, healthy_only=True,
                     cluster=None, metadata=None)
await get_one_healthy_instance(app, service_name, group=None, strategy=None,
                               cluster=None, metadata=None)
normalize_instance(instance)
await get_config(app, data_id=None, group=None)
get_status(app)
```

`get_status()` is a local-only, side-effect-free 16-field lifecycle snapshot.
When enabled, `GET /health/nacos` exposes a stable seven-field local health
response and never contacts Nacos.

## Design guarantees

- Configuration precedence is defaults, constructor config, then `init_app()` config.
- Each application and PID owns an isolated runtime and defensive config snapshot.
- Repeated initialization by the same extension is idempotent.
- User lifespan handlers are composed with the plugin lifespan.
- Registration is non-blocking and uses a last-command-wins state machine.
- Only one lifecycle worker and one Naming RPC run per application/PID.
- Successful registration identity is cached for exact deregistration.
- Transient transport failures recover at a low frequency; deterministic failures stop.
- Preload/fork workers rebuild locks, client and runtime state in the child process.
- Raw SDK logs are silenced because they can contain credentials or config content.

## Documentation

- [Quick start](docs/quickstart.md)
- [Configuration](docs/configuration.md)
- [API reference](docs/api-reference.md)
- [Registration](docs/service-registration.md)
- [Discovery](docs/service-discovery.md)
- [Configuration center](docs/config-center.md)
- [Health check](docs/health-check.md)
- [Production](docs/production.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Compatibility](docs/compatibility.md)
- [Release process](docs/release.md)

## Development

Use the repository environment and run the complete gate:

```bash
.venv/Scripts/python -m ruff check fastapi_nacos tests examples scripts
.venv/Scripts/python -m mypy fastapi_nacos
.venv/Scripts/python -m pytest
.venv/Scripts/python -m build
.venv/Scripts/python -m twine check dist/*
```

Integration tests are opt-in and must use a disposable Nacos 2.3.2 instance:

```bash
docker compose -f examples/docker-compose-nacos.yml up -d
NACOS_INTEGRATION=1 .venv/Scripts/python -m pytest -m integration
```

## License and provenance

The repository is licensed under GPLv3. It is adapted from Flask-Nacos
(Apache-2.0); see [NOTICE](NOTICE) for attribution and scope.
