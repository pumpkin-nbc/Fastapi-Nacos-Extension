# Production deployment

Use an application factory, configure an explicit routable service IP/port,
keep one plugin instance per process, and let FastAPI manage lifespan. Example:

```bash
uvicorn examples.production_app:app --host 0.0.0.0 --port 8000 --workers 4
```

For Gunicorn on Linux:

```bash
gunicorn examples.production_app:app -k uvicorn.workers.UvicornWorker -w 4 --preload
```

`--preload` is supported: inherited locks, runtime and client references are
discarded and rebuilt in each child PID. Each worker registers its own instance
and deregisters it during lifespan shutdown when
`NACOS_DEREGISTER_ON_EXIT=True`. Ensure termination grace exceeds the Nacos SDK
timeout. Do not use the health endpoint as a remote Nacos connectivity probe.

Prefer explicit credentials from a secret manager, never log config mappings,
and keep raw SDK loggers disabled. Run only one ASGI lifespan per worker.

