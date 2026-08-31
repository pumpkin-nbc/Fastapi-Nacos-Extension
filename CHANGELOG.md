# Changelog

## 0.1.0

- Initial FastAPI port of Flask-Nacos 1.1.1.
- Uses the `fastapi-nacos-extension` distribution and
  `fastapi_nacos_extension` import namespace to avoid the unrelated PyPI project.
- Async-first service registration, discovery, configuration and shutdown APIs.
- FastAPI lifespan integration, local health route and per-app/PID isolation.
- Compatibility coverage from FastAPI 0.112.2 through 0.141.1 while retaining
  Python 3.8 as the minimum supported runtime.
