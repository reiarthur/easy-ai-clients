"""Media asset helpers."""

from __future__ import annotations

import importlib

from .._error_utils import attach_error, error_message

__all__ = ["upload_asset", "delete_asset", "available_apis"]

_AVAILABLE_APIS = ("heygen",)


def available_apis():
    return _AVAILABLE_APIS


def _load(api):
    if not isinstance(api, str) or not api:
        raise ValueError(f"media operations require api. Available APIs: {', '.join(_AVAILABLE_APIS)}.")
    if api not in _AVAILABLE_APIS:
        raise ValueError(f"Unknown media API '{api}'. Available APIs: {', '.join(_AVAILABLE_APIS)}.")
    return importlib.import_module(f"._apis.{api}", __name__)


def upload_asset(file, *, api, **kwargs):
    try:
        return _load(api).upload_asset(file, **kwargs)
    except Exception as exc:
        return _failure(exc, api=api, operation="upload_asset")


def delete_asset(asset_id, *, api, confirm=False, **kwargs):
    try:
        return _load(api).delete_asset(asset_id, confirm=confirm, **kwargs)
    except Exception as exc:
        return _failure(exc, api=api, operation="delete_asset")


def _failure(exc, *, api, operation):
    message = error_message(exc)
    return attach_error(
        {"provider": api, "operation": operation, "data": None, "raw_response": {}, "warnings": message},
        exc,
        provider=api,
        operation=operation,
    )

