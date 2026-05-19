"""Account helper dispatchers."""

from __future__ import annotations

import importlib

from .._error_utils import attach_error, error_message

__all__ = ["get_current_user", "available_apis"]

_AVAILABLE_APIS = ("heygen",)


def available_apis():
    return _AVAILABLE_APIS


def _load(api):
    if not isinstance(api, str) or not api:
        raise ValueError(f"account operations require api. Available APIs: {', '.join(_AVAILABLE_APIS)}.")
    if api not in _AVAILABLE_APIS:
        raise ValueError(f"Unknown account API '{api}'. Available APIs: {', '.join(_AVAILABLE_APIS)}.")
    return importlib.import_module(f"._apis.{api}", __name__)


def get_current_user(*, api, **kwargs):
    try:
        return _load(api).get_current_user(**kwargs)
    except Exception as exc:
        message = error_message(exc)
        return attach_error(
            {"provider": api, "data": None, "raw_response": {}, "warnings": message},
            exc,
            provider=api,
            operation="get_current_user",
        )

