# 配置中心

`await nacos.get_config(app, "application.yaml", group="DEFAULT_GROUP")` 原样返回 SDK 文本。插件不会解析 YAML/JSON，不写入应用状态，也不安装动态监听器。
