"""Shared normalized error helpers for public dispatchers."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

_SECRET_PATTERNS = (
    (
        re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|key|token)?\s*)[^\s,;]+"),
        r"\1[redacted]",
    ),
    (
        re.compile(r"(?i)\b(bearer|key|token)\s+[A-Za-z0-9._~+/=-]{8,}"),
        r"\1 [redacted]",
    ),
    (
        re.compile(r"(?i)\b(api[_-]?key|token|secret)(\s*[:=]\s*)[^\s,;]+"),
        r"\1\2[redacted]",
    ),
)


def sanitize_error_message(error: Any) -> str:
    """Return a compact provider/runtime error message with secrets redacted."""

    message = " ".join(str(error or "").split())
    for value in os.environ.values():
        secret = str(value or "").strip()
        if len(secret) >= 8 and secret in message:
            message = message.replace(secret, "[redacted]")
    for pattern, replacement in _SECRET_PATTERNS:
        message = pattern.sub(replacement, message)
    return message[:1500]


def build_error(
    error: Any,
    *,
    provider: str | None = None,
    operation: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Build the public `error` object used by normalized failure results."""

    return {
        "type": type(error).__name__ if error is not None else "Error",
        "message": sanitize_error_message(error),
        "provider": provider,
        "operation": operation,
        "model": model,
    }


def error_message(error: Any) -> str:
    """Return only the redacted message portion of a public error."""

    return sanitize_error_message(error)


def attach_error(
    result: Mapping[str, Any],
    error: Any,
    *,
    provider: str | None = None,
    operation: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Return a copy of `result` with a normalized `error` object attached."""

    output = dict(result)
    output["error"] = build_error(error, provider=provider, operation=operation, model=model)
    return output
