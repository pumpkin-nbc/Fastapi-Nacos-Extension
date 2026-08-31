# API 参考

`FastAPINacos(app=None, config=None)` 与 `init_app(app, config=None)` 是同步且无网络副作用的。可能访问网络的公开接口均为异步：`get_client`、`register_instance`、`deregister_instance`、`list_instances`、`get_one_healthy_instance`、`get_config`。

本地同步接口包括 `get_cached_client(app)`、`get_config_snapshot(app)`、`normalize_instance(instance)` 与 `get_status(app)`。

`get_status()` 固定包含 16 个字段：`enabled`、`pid`、`client_created`、`service_name`、`group_name`、`cluster_name`、`service_ip`、`service_port`、`target_registered`、`registered`、`operation_running`、`last_error`、`heartbeat_state`、`last_heartbeat_success_at`、`last_heartbeat_failure_at`、`heartbeat_error_type`。

包导出统一异常基类、配置、Client、校验、注册、注销、发现与日志异常，以及 `__version__`。

