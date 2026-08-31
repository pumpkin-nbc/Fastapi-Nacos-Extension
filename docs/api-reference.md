# API reference

`FastAPINacos(app=None, config=None)` and `init_app(app, config=None)` are
synchronous and network-free. The network-capable API is async:

- `await get_client(app)` lazily returns the PID-local SDK client.
- `await register_instance(app)` submits a non-blocking registration target.
- `await deregister_instance(app)` returns whether the unregistered target was accepted/succeeded.
- `await list_instances(...)` returns filtered instances.
- `await get_one_healthy_instance(...)` selects `first`, `random`, or `weight`.
- `await get_config(app, data_id=None, group=None)` returns raw text or `None`.

Local synchronous helpers are `get_cached_client(app)`,
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

