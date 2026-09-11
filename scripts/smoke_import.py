"""Minimal import and lazy-initialization smoke test for a clean environment."""

from fastapi import FastAPI

from fastapi_nacos_extension import FastAPINacos, __version__


def main() -> None:
    app = FastAPI()
    extension = FastAPINacos(app, {"NACOS_ENABLED": False})
    assert __version__ == "0.1.1"
    assert extension.get_cached_client(app) is None
    assert extension.get_client_sync(app) is None
    assert extension.register_instance_sync(app) is None
    assert extension.deregister_instance_sync(app) is True
    assert extension.list_instances_sync(app, "disabled-service") == []
    assert extension.get_one_healthy_instance_sync(app, "disabled-service") is None
    assert extension.get_config_sync(app) is None
    assert extension.get_status(app)["enabled"] is False
    print(f"fastapi-nacos-extension {__version__} smoke import passed")


if __name__ == "__main__":
    main()
