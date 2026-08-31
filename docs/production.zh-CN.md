# 生产部署

建议使用应用工厂，明确配置可路由的服务 IP/端口，每个进程复用一个插件实例，并由 FastAPI 管理 lifespan。

```bash
uvicorn examples.production_app:app --host 0.0.0.0 --port 8000 --workers 4
gunicorn examples.production_app:app -k uvicorn.workers.UvicornWorker -w 4 --preload
```

支持 `--preload`：子 PID 会丢弃继承的锁、Runtime 与 Client，并重建进程内状态。每个 Worker 注册自己的实例；`NACOS_DEREGISTER_ON_EXIT=True` 时在 lifespan 关闭阶段注销。终止宽限时间应大于 SDK 超时。

凭证应来自密钥管理系统，不要记录完整配置映射；原始 SDK 日志应保持禁用。本地健康路由不是远程 Nacos 连通性探针。

