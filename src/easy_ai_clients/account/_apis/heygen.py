"""HeyGen v3 account adapter."""

from __future__ import annotations

from typing import Any

from ... import _heygen


def get_current_user(**kwargs: Any):
    raw = _heygen.request_json(
        "GET",
        "/v3/users/me",
        params={key: value for key, value in kwargs.items() if key != "timeout_seconds"},
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}

