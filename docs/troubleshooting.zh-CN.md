# 故障排查

- 启动前出现 `NacosValidationError` 通常表示自动注册配置无效，请设置非空服务名与合法明确端口。
- 关闭自动注册后，连接与注册校验会推迟到对应手动调用。
- `last_error` 只暴露异常类型，不包含网络异常原文或凭证。
- `target_registered=True`、`registered=False`、`operation_running=True` 表示后台收敛或瞬时故障恢复仍在进行。
- 首次操作前 `client_created=False` 是惰性初始化的正常表现。
- 健康路由缺失可能是功能关闭，或路径已被应用占用。
- 发现结果为空可能是服务无实例、过滤条件移除或异常实例被跳过。
- 所有应用相关方法都必须传入由同一扩展实例初始化的明确 app。

容器诊断可开启 `NACOS_LOG_ENABLED=True` 并关闭文件日志；原始 SDK 日志仍会保持隔离。

