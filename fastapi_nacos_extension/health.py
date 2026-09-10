"""Local-only FastAPI health endpoint for FastAPI-Nacos-Extension."""

import logging
from typing import TYPE_CHECKING, Any, Dict

from fastapi import FastAPI

if TYPE_CHECKING:
    from .extension import FastAPINacos

logger = logging.getLogger("fastapi_nacos_extension")

HEALTH_ENDPOINT = "fastapi_nacos_extension_health"


def build_health_payload(
    extension: "FastAPINacos", app: FastAPI
) -> Dict[str, Any]:
    """Build the fixed response exclusively from local extension state."""
    status = extension.get_status(app)
    enabled = status["enabled"]
    registered = status["registered"]
    target_registered = status["target_registered"]
    operation_running = status["operation_running"]
    last_error = status["last_error"]

    if not enabled:
        overall = "disabled"
    elif registered == target_registered:
        overall = "ok"
    elif operation_running and last_error is None:
        overall = "ok"
    else:
        overall = "error"

    return {
        "status": overall,
        "enabled": enabled,
        "client_created": status["client_created"],
        "target_registered": target_registered,
        "registered": registered,
        "operation_running": operation_running,
        "last_error": last_error,
    }


def register_health_route(app: FastAPI, extension: "FastAPINacos") -> bool:
    """Register the configured GET endpoint without replacing user routes."""
    state = getattr(app.state, "nacos", None) or {}
    cfg = state.get("config") or {}
    path = cfg.get("NACOS_HEALTH_CHECK_PATH") or "/health/nacos"

    for route in app.routes:
        if getattr(route, "name", None) == HEALTH_ENDPOINT:
            logger.info("Health check route already registered; skipping (path=%s)", path)
            return False
        if getattr(route, "path", None) == path:
            logger.info("Health check path %s already in use; skipping registration", path)
            return False

    async def health_view() -> Dict[str, Any]:
        return build_health_payload(extension, app)

    app.add_api_route(
        path,
        health_view,
        methods=["GET"],
        name=HEALTH_ENDPOINT,
        tags=["Nacos"],
        summary="FastAPI-Nacos-Extension local health",
    )
    logger.info("Health check route registered (path=%s)", path)
    return True


__all__ = ["register_health_route", "build_health_payload", "HEALTH_ENDPOINT"]
