# 更新日志

## 0.1.0

- 完成首个面向 Nacos 2.x 的生产级 FastAPI 集成版本。
- 项目采用 Apache License 2.0 开源许可证。
- 使用 `fastapi-nacos-extension` 发行名和 `fastapi_nacos_extension`
  导入命名空间，避免与 PyPI 上无关的同名项目冲突。
- 提供异步优先的注册、发现、配置读取和关闭接口。
- 支持 FastAPI lifespan、本地健康路由以及 app/PID 隔离。
- 在保持 Python 3.8 最低运行要求的同时，将 FastAPI 兼容测试扩展至
  0.112.2—0.141.1，并连续覆盖 Python 3.8—3.14。
- 增加 Trusted Publishing：支持 TestPyPI 手动预演和标签驱动的 PyPI 自动发布，
  两条发布路径使用同一份已验证产物。
