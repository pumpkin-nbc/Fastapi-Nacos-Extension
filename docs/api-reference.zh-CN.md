# API 参考

`FastAPINacos(app=None, config=None)` 与 `init_app(app, config=None)` 是同步且无网络副作用的。可能访问网络的操作同时提供异步接口和同步接口：

- `await get_client(app)` / `get_client_sync(app)`
- `await register_instance(app)` / `register_instance_sync(app)`
- `await deregister_instance(app)` / `deregister_instance_sync(app)`
- `await list_instances(...)` / `list_instances_sync(...)`
- `await get_one_healthy_instance(...)` / `get_one_healthy_instance_sync(...)`
- `await get_config(...)` / `get_config_sync(...)`

两种形式的参数、返回值、异常与状态机语义保持一致。异步接口通过线程池调用同步 Nacos SDK，不阻塞 ASGI 事件循环；`_sync` 接口在当前调用线程中执行，适用于普通同步代码，不应在异步路由中直接调用。注册接口无论采用哪种形式都只提交注册目标，并保持非阻塞收敛语义。

本地同步接口还包括 `get_cached_client(app)`、`get_config_snapshot(app)`、`normalize_instance(instance)` 与 `get_status(app)`。

`get_status()` 固定包含 16 个字段：`enabled`、`pid`、`client_created`、`service_name`、`group_name`、`cluster_name`、`service_ip`、`service_port`、`target_registered`、`registered`、`operation_running`、`last_error`、`heartbeat_state`、`last_heartbeat_success_at`、`last_heartbeat_failure_at`、`heartbeat_error_type`。

包导出统一异常基类、配置、Client、校验、注册、注销、发现与日志异常，以及 `__version__`。
