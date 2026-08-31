# Configuration reference

Settings are merged in this order: built-in defaults, constructor `config`,
then the mapping passed to `init_app()`. Unknown keys are ignored. Each app
receives an isolated snapshot; metadata dictionaries are copied.

| Key | Default | Purpose |
| --- | --- | --- |
| `NACOS_ENABLED` | `True` | Enable all Nacos capabilities. |
| `NACOS_SERVER_ADDR` | `127.0.0.1:8848` | SDK server address list. |
| `NACOS_NAMESPACE_ID` | empty | Namespace identifier. |
| `NACOS_USERNAME` / `NACOS_PASSWORD` | `None` | Paired username authentication. |
| `NACOS_ACCESS_KEY` / `NACOS_SECRET_KEY` | `None` | Paired AK/SK authentication; mutually exclusive with username auth. |
| `NACOS_GROUP_NAME` | `DEFAULT_GROUP` | Default discovery group. |
| `NACOS_AUTO_REGISTER` | `True` | Start background registration during lifespan startup. |
| `NACOS_DEREGISTER_ON_EXIT` | `True` | Perform bounded deregistration at lifespan/process exit. |
| `NACOS_SERVICE_NAME` | `None` | Local service name; required for registration. |
| `NACOS_SERVICE_IP` | `None` | Local service IP; auto-detected when omitted. |
| `NACOS_SERVICE_PORT` | `None` | Local service port; required, never guessed. |
| `NACOS_SERVICE_GROUP` | `DEFAULT_GROUP` | Registration group. |
| `NACOS_SERVICE_CLUSTER` | `DEFAULT` | Registration cluster. |
| `NACOS_SERVICE_WEIGHT` | `1.0` | Positive instance weight. |
| `NACOS_SERVICE_METADATA` | `{}` | Instance metadata dictionary. |
| `NACOS_SERVICE_EPHEMERAL` | `True` | Register an ephemeral instance. Must be a real bool. |
| `NACOS_SERVICE_HEARTBEAT_INTERVAL` | `5.0` | Positive heartbeat interval for ephemeral instances. |
| `NACOS_SERVICE_HEALTHY` | `True` | Initial SDK healthy flag. |
| `NACOS_SERVICE_ENABLED` | `True` | Initial SDK enabled flag. |
| `NACOS_CONFIG_ENABLED` | `True` | Enable configuration reads. |
| `NACOS_CONFIG_DATA_ID` | `None` | Default data ID. |
| `NACOS_CONFIG_GROUP` | `DEFAULT_GROUP` | Default config group. |
| `NACOS_RETRY_ENABLED` | `True` | Enable finite retry and transient recovery. |
| `NACOS_RETRY_TIMES` | `3` | Attempts in one finite retry round. |
| `NACOS_RETRY_INTERVAL` | `1.0` | Seconds between finite attempts. |
| `NACOS_REQUEST_TIMEOUT` | `5.0` | Config read timeout. |
| `NACOS_HEALTH_CHECK_ENABLED` | `False` | Add the local health route. |
| `NACOS_HEALTH_CHECK_PATH` | `/health/nacos` | Health path; an existing path is never replaced. |
| `NACOS_DISCOVERY_STRATEGY` | `first` | `first`, `random`, or `weight`. |
| `NACOS_DISCOVERY_CLUSTER` | `None` | Default discovery cluster filter. |
| `NACOS_DISCOVERY_METADATA` | `{}` | Default metadata filter. |
| `NACOS_INSTANCE_NORMALIZE` | `True` | Normalize SDK instance shapes. |
| `NACOS_LOG_ENABLED` | `False` | Enable safe plugin logging. |
| `NACOS_LOG_LEVEL` | `INFO` | Plugin log level. |
| `NACOS_LOG_CONSOLE_ENABLED` | `True` | Add a colored console handler. |
| `NACOS_LOG_FILE_ENABLED` | `True` | Add a plugin-only file handler. |
| `NACOS_LOG_PATH` | `./logs` | Log directory. |
| `NACOS_LOG_FILENAME` | `fastapi-nacos.log` | Log filename without a path. |
| `NACOS_LOG_FORMAT` | timestamped format | Python logging format. |
| `NACOS_LOG_PROPAGATE` | `True` | Propagate safe plugin records. |
| `NACOS_LOG_MAX_BYTES` | `10485760` | Rotation threshold; `0` disables rotation. |
| `NACOS_LOG_BACKUP_COUNT` | `5` | Rotated backups. |

Registration-only fields are validated only when auto or explicit registration
is requested. Connection fields are validated locally before client creation.

