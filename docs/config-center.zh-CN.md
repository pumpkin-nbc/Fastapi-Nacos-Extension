# 配置中心

`await nacos.get_config(app, "application.yaml", group="DEFAULT_GROUP")` 原样返回 SDK 文本；同步代码可使用返回值和异常行为一致的 `nacos.get_config_sync(...)`。插件不会解析 YAML/JSON，不写入应用状态，也不安装动态监听器。
