"""Custom exception hierarchy for fastapi-nacos-extension."""


class FastAPINacosError(Exception):
    """Base exception for all fastapi-nacos-extension errors."""


class NacosConfigError(FastAPINacosError):
    """Raised when configuration is invalid or a config operation fails."""


class NacosClientError(FastAPINacosError):
    """Raised when the underlying Nacos client cannot be created or used."""


class NacosValidationError(NacosConfigError):
    """Raised when deterministic Nacos input or numeric config validation fails.

    Subclasses :class:`NacosConfigError` so that code catching configuration
    errors also catches validation errors.
    """


class NacosRegistrationError(FastAPINacosError):
    """Raised when service registration fails."""


class NacosDeregistrationError(FastAPINacosError):
    """Raised when service deregistration fails."""


class NacosDiscoveryError(FastAPINacosError):
    """Raised when a service discovery operation fails."""


class NacosLoggingError(FastAPINacosError):
    """Raised when logging configuration is invalid or a logging setup step fails."""


__all__ = [
    "FastAPINacosError",
    "NacosConfigError",
    "NacosClientError",
    "NacosValidationError",
    "NacosRegistrationError",
    "NacosDeregistrationError",
    "NacosDiscoveryError",
    "NacosLoggingError",
]

