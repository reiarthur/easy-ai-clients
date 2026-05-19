"""Webhook helper dispatchers."""

from __future__ import annotations

import importlib

from .._error_utils import attach_error, error_message

__all__ = [
    "list_endpoints",
    "create_endpoint",
    "update_endpoint",
    "delete_endpoint",
    "rotate_secret",
    "list_event_types",
    "list_events",
    "available_apis",
]

_AVAILABLE_APIS = ("heygen",)


def available_apis():
    return _AVAILABLE_APIS


def _load(api):
    if not isinstance(api, str) or not api:
        raise ValueError(f"webhook operations require api. Available APIs: {', '.join(_AVAILABLE_APIS)}.")
    if api not in _AVAILABLE_APIS:
        raise ValueError(f"Unknown webhook API '{api}'. Available APIs: {', '.join(_AVAILABLE_APIS)}.")
    return importlib.import_module(f"._apis.{api}", __name__)


def _call(api, operation, *args, **kwargs):
    try:
        return getattr(_load(api), operation)(*args, **kwargs)
    except Exception as exc:
        message = error_message(exc)
        return attach_error(
            {"provider": api, "operation": operation, "data": None, "raw_response": {}, "warnings": message},
            exc,
            provider=api,
            operation=operation,
        )


def list_endpoints(*, api, **kwargs):
    return _call(api, "list_endpoints", **kwargs)


def create_endpoint(url, *, api, **kwargs):
    return _call(api, "create_endpoint", url, **kwargs)


def update_endpoint(endpoint_id, *, api, **kwargs):
    return _call(api, "update_endpoint", endpoint_id, **kwargs)


def delete_endpoint(endpoint_id, *, api, confirm=False, **kwargs):
    return _call(api, "delete_endpoint", endpoint_id, confirm=confirm, **kwargs)


def rotate_secret(endpoint_id, *, api, **kwargs):
    return _call(api, "rotate_secret", endpoint_id, **kwargs)


def list_event_types(*, api, **kwargs):
    return _call(api, "list_event_types", **kwargs)


def list_events(*, api, **kwargs):
    return _call(api, "list_events", **kwargs)

