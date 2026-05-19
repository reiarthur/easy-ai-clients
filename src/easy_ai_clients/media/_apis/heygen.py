"""HeyGen v3 media asset adapter."""

from __future__ import annotations

from typing import Any

from ... import _heygen


def upload_asset(file, **kwargs: Any):
    raw = _heygen.upload_asset(file, timeout_seconds=kwargs.get("timeout_seconds"))
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}


def delete_asset(asset_id, *, confirm=False, **kwargs: Any):
    if confirm is not True:
        raise ValueError("Set confirm=True to execute destructive HeyGen delete operations.")
    raw = _heygen.request_json(
        "DELETE",
        f"/v3/assets/{_heygen.quote_path(asset_id)}",
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}

