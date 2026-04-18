"""Exceções públicas disparadas por easy-ai-clients.

Última atualização: 2026-04-18
"""

from ._core.exceptions import (
    ConfigurationError,
    EasyAiClientError,
    IncompatibleParameterError,
    InvalidParameterError,
    InvalidProviderResponseError,
    JobFailedError,
    MissingCredentialError,
    PricingUnavailableError,
    ProviderTimeoutError,
    TemporaryDownloadError,
    UnsupportedModelError,
    UnsupportedProviderError,
)

__all__ = [
    "ConfigurationError",
    "EasyAiClientError",
    "IncompatibleParameterError",
    "InvalidParameterError",
    "InvalidProviderResponseError",
    "JobFailedError",
    "MissingCredentialError",
    "PricingUnavailableError",
    "ProviderTimeoutError",
    "TemporaryDownloadError",
    "UnsupportedModelError",
    "UnsupportedProviderError",
]
