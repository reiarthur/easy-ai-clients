"""Custom exceptions used across the integration layer."""

from __future__ import annotations

from dataclasses import dataclass


class ApiImageError(Exception):
    """Base exception for controllable integration failures."""


class InputValidationError(ApiImageError):
    """Raised when a public input cannot be normalized safely."""


class UnsupportedFeatureError(ApiImageError):
    """Raised when the requested provider/model feature is unsupported."""


class ProviderResponseError(ApiImageError):
    """Raised when a provider returns an unexpected or failed response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
        is_transient: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.is_transient = is_transient


@dataclass(frozen=True)
class BlockedOperation:
    """Represents a provider-side block, moderation event or external failure."""

    warning: str
    request_id: str = ""
    cust_usd: float = 0.0

