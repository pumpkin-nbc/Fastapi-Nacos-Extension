# 服务发现

`list_instances()` 支持 group、healthy、cluster 与 metadata 过滤；`get_one_healthy_instance()` 支持 `first`、`random`、`weight` 策略。适配器兼容 SDK 返回列表、`hosts`、`instances` 和嵌套 `data` 等结构。

标准化实例包含 IP、端口、服务/集群名、权重、healthy/enabled/ephemeral 标志和复制后的 metadata。单条异常实例会跳过，不影响其他结果。

