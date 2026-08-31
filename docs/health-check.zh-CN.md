# 健康检查

设置 `NACOS_HEALTH_CHECK_ENABLED=True` 可添加 `GET /health/nacos`，路径可用 `NACOS_HEALTH_CHECK_PATH` 修改。路由进入 OpenAPI、只注册一次，并且不会覆盖应用已有的同路径路由。

响应固定 7 字段：`status`、`enabled`、`client_created`、`target_registered`、`registered`、`operation_running`、`last_error`。它只读取本地状态，不调用 SDK。心跳观测仅出现在 16 字段的 `get_status()` 中。

