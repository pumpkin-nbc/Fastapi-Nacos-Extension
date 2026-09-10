"""Minimal import and lazy-initialization smoke test for a clean environment."""

from fastapi import FastAPI

from fastapi_nacos_extension import FastAPINacos, __version__


def main() -> None:
    app = FastAPI()
    extension = FastAPINacos(app, {"NACOS_ENABLED": False})
    assert __version__ == "0.1.0"
    assert extension.get_cached_client(app) is None
    assert extension.get_status(app)["enabled"] is False
    print(f"fastapi-nacos-extension {__version__} smoke import passed")


if __name__ == "__main__":
    main()
