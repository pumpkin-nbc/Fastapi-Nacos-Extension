# Health check

Set `NACOS_HEALTH_CHECK_ENABLED=True` to add `GET /health/nacos`, or configure
`NACOS_HEALTH_CHECK_PATH`. The route is included in OpenAPI, is registered once,
and never replaces a user route at the same path.

The endpoint is local-only and has exactly seven fields: `status`, `enabled`,
`client_created`, `target_registered`, `registered`, `operation_running`, and
`last_error`. It performs no SDK call. Heartbeat observations remain available
through the 16-field `get_status()` contract and do not change the health body.

