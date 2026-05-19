"""HeyGen v3 avatar creation adapter."""

from __future__ import annotations

from typing import Any

from .... import _heygen
from ..._heygen_common import AVATAR_MODEL, cost_metadata, passthrough_payload
from ..._shared import normalize_result


def create_avatar(image_path=None, image_url=None, name=None, voice=None, **kwargs: Any):
    avatar_type = kwargs.pop("type", None)
    prompt = kwargs.pop("prompt", None)
    video_path = kwargs.pop("video_path", kwargs.pop("file_path", None))
    video_url = kwargs.pop("video_url", kwargs.pop("file_url", None))
    if prompt and not avatar_type:
        avatar_type = "prompt"
    elif video_path or video_url:
        avatar_type = "digital_twin"
    else:
        avatar_type = avatar_type or "photo"
    if not name:
        raise ValueError("name is required.")
    if avatar_type == "prompt":
        base = {"type": "prompt", "name": name, "prompt": prompt}
    elif avatar_type == "digital_twin":
        base = {
            "type": "digital_twin",
            "name": name,
            "file": _heygen.asset_input(video_url or video_path, field_name="file", allow_base64=False),
        }
    else:
        base = {
            "type": "photo",
            "name": name,
            "file": _heygen.asset_input(image_url or image_path, field_name="file", allow_base64=True),
        }
    payload = passthrough_payload(base, kwargs)
    if voice is not None:
        payload["voice_id"] = voice
    raw = _heygen.request_json(
        "POST",
        "/v3/avatars",
        payload=payload,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    item = _heygen.data(raw)
    group = item.get("avatar_group") if isinstance(item, dict) else None
    avatar_item = item.get("avatar_item") if isinstance(item, dict) else None
    avatar_id = None
    if isinstance(avatar_item, dict):
        avatar_id = avatar_item.get("id")
    if not avatar_id and isinstance(group, dict):
        avatar_id = group.get("id")
    cost = cost_metadata(kwargs)
    result = normalize_result(
        "heygen",
        kwargs.get("model") or AVATAR_MODEL,
        _heygen.normalize_status(
            (avatar_item or group or {}).get("status") if isinstance(avatar_item or group, dict) else None
        ),
        avatar_id,
        None,
        None,
        cost["cost_usd"],
        cost["cost_is_estimated"],
        cost["cost_source"],
        raw,
        {"avatar_id": avatar_id, "avatar_group": group, "avatar_item": avatar_item},
    )
    return result
