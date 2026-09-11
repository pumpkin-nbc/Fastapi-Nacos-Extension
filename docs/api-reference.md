# API reference

`FastAPINacos(app=None, config=None)` and `init_app(app, config=None)` are
synchronous and network-free. Every network-capable operation offers matching
async and synchronous forms:

- `await get_client(app)` / `get_client_sync(app)`
- `await register_instance(app)` / `register_instance_sync(app)`
- `await deregister_instance(app)` / `deregister_instance_sync(app)`
- `await list_instances(...)` / `list_instances_sync(...)`
- `await get_one_healthy_instance(...)` / `get_one_healthy_instance_sync(...)`
- `await get_config(...)` / `get_config_sync(...)`

Both forms have matching arguments, return values, exceptions, and state-machine
semantics. Async methods move calls to the thread pool and do not block the ASGI
event loop. `_sync` methods run in the calling thread and are intended for
synchronous code; do not call them directly from an async route. Registration
only submits the target in both forms and retains non-blocking convergence.

Additional local synchronous helpers are `get_cached_client(app)`,
`get_config_snapshot(app)`, `normalize_instance(instance)`, and
`get_status(app)`.

`get_status()` always contains exactly: `enabled`, `pid`, `client_created`,
`service_name`, `group_name`, `cluster_name`, `service_ip`, `service_port`,
`target_registered`, `registered`, `operation_running`, `last_error`,
`heartbeat_state`, `last_heartbeat_success_at`,
`last_heartbeat_failure_at`, and `heartbeat_error_type`.

The package exports `FastAPINacosError`, `NacosConfigError`,
`NacosClientError`, `NacosValidationError`, `NacosRegistrationError`,
`NacosDeregistrationError`, `NacosDiscoveryError`, `NacosLoggingError`, and
`__version__`.
