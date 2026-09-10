"""FastAPI-Nacos-Extension: Nacos lifecycle, discovery and configuration for FastAPI."""

from .exceptions import (
    FastAPINacosError,
    NacosClientError,
    NacosConfigError,
    NacosDeregistrationError,
    NacosDiscoveryError,
    NacosLoggingError,
    NacosRegistrationError,
    NacosValidationError,
)
from .extension import FastAPINacos

__version__ = "0.1.0"

__all__ = [
    "FastAPINacos",
    "FastAPINacosError",
    "NacosConfigError",
    "NacosClientError",
    "NacosValidationError",
    "NacosRegistrationError",
    "NacosDeregistrationError",
    "NacosDiscoveryError",
    "NacosLoggingError",
    "__version__",
]
