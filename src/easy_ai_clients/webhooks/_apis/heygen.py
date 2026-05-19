"""HeyGen v3 webhook adapter."""

from __future__ import annotations

from typing import Any

from ... import _heygen


def _result(raw):
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}


def _params(kwargs):
    return {key: value for key, value in kwargs.items() if key != "timeout_seconds"}


def list_endpoints(**kwargs: Any):
    return _result(_heygen.request_json("GET", "/v3/webhooks/endpoints", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def create_endpoint(url, **kwargs: Any):
    payload = {"url": url, **kwargs}
    payload.pop("timeout_seconds", None)
    return _result(_heygen.request_json("POST", "/v3/webhooks/endpoints", payload=payload, timeout_seconds=kwargs.get("timeout_seconds")))


def update_endpoint(endpoint_id, **kwargs: Any):
    payload = dict(kwargs)
    payload.pop("timeout_seconds", None)
    return _result(_heygen.request_json("PATCH", f"/v3/webhooks/endpoints/{_heygen.quote_path(endpoint_id)}", payload=payload, timeout_seconds=kwargs.get("timeout_seconds")))


def delete_endpoint(endpoint_id, *, confirm=False, **kwargs: Any):
    if confirm is not True:
        raise ValueError("Set confirm=True to execute destructive HeyGen delete operations.")
    return _result(_heygen.request_json("DELETE", f"/v3/webhooks/endpoints/{_heygen.quote_path(endpoint_id)}", timeout_seconds=kwargs.get("timeout_seconds")))


def rotate_secret(endpoint_id, **kwargs: Any):
    return _result(_heygen.request_json("POST", f"/v3/webhooks/endpoints/{_heygen.quote_path(endpoint_id)}/rotate-secret", timeout_seconds=kwargs.get("timeout_seconds")))


def list_event_types(**kwargs: Any):
    return _result(_heygen.request_json("GET", "/v3/webhooks/event-types", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def list_events(**kwargs: Any):
    return _result(_heygen.request_json("GET", "/v3/webhooks/events", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))

