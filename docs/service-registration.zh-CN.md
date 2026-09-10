# 服务注册

自动注册在 FastAPI lifespan 启动阶段提交后台收敛命令；手动注册使用 `await nacos.register_instance(app)`。两者共用“最后命令优先”状态机、有限重试、保守故障分类和仅针对明确瞬时故障的低频恢复。

每应用/PID 最多一个 Worker 和一个 Naming RPC。成功后缓存准确的服务、分组、集群、IP、端口与 ephemeral 标识；即使配置随后变化，注销仍使用缓存身份。关闭等待受 SDK 超时上界限制。

