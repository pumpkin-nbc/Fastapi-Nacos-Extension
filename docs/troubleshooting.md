# Troubleshooting

- `NacosValidationError` before startup means auto-registration configuration is invalid. Set a non-empty service name and a legal explicit port.
- A manual call can surface deferred connection/registration validation when auto-registration is disabled.
- `last_error` exposes only an exception type, never raw network or credential-bearing details.
- `target_registered=True`, `registered=False`, `operation_running=True` means background convergence or transient recovery is active.
- `client_created=False` is normal before startup or the first operation because initialization is lazy.
- A missing health route usually means the feature is disabled or its path was already owned by the application.
- Discovery returning an empty list can mean the SDK returned no rows, filters removed them, or malformed rows were skipped.
- Every public app-scoped method requires the same explicit app that was initialized by that extension instance.

Enable safe plugin logging with `NACOS_LOG_ENABLED=True` and disable file output
when diagnosing in containers. SDK logs stay intentionally silent.

