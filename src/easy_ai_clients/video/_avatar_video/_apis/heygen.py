"""HeyGen v3 avatar-video adapter."""

from __future__ import annotations

from typing import Any

from .... import _heygen
from ..._heygen_common import (
    VIDEO_MODEL,
    audio_fields,
    media_union,
    passthrough_payload,
    submit_video,
)

PHOTO_AVATAR_MODEL = "avatar_iv/photo_avatar"
MODEL_ALIASES = {
    "heygen_photo_avatar": PHOTO_AVATAR_MODEL,
    PHOTO_AVATAR_MODEL: PHOTO_AVATAR_MODEL,
}


def _selected_model(kwargs):
    selected = kwargs.get("model") or VIDEO_MODEL
    return MODEL_ALIASES.get(str(selected).strip(), selected)


def _photo_avatar_cost(kwargs):
    value = kwargs.get("billing_cost_usd", kwargs.get("estimated_cost_usd"))
    if value is not None:
        return {
            "cost_usd": float(value),
            "cost_is_estimated": True,
            "cost_source": "caller_estimate",
        }
    duration = kwargs.get("billing_duration_seconds", kwargs.get("duration_seconds", kwargs.get("duration")))
    if duration is None:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
        }
    resolution = kwargs.get("resolution", "720p")
    rate = 0.0667 if resolution == "4k" else 0.05
    return {
        "cost_usd": 1.0 + float(duration) * rate,
        "cost_is_estimated": True,
        "cost_source": "heygen_photo_avatar_local_pricing_evidence_2026-06-23",
    }


def _photo_avatar_id(raw):
    item = _heygen.data(raw)
    if not isinstance(item, dict):
        raise RuntimeError("HeyGen Photo Avatar creation did not return a data object.")
    avatar_item = item.get("avatar_item")
    group = item.get("avatar_group")
    if isinstance(avatar_item, dict) and avatar_item.get("id"):
        return avatar_item["id"]
    if isinstance(group, dict) and group.get("id"):
        return group["id"]
    raise RuntimeError("HeyGen Photo Avatar creation did not return avatar_item.id.")


def _create_photo_avatar(image_path, image_url, kwargs):
    image = media_union(
        image_path,
        image_url,
        kwargs.pop("image_asset_id", None),
        field_name="image",
        allow_base64=True,
    )
    if not image:
        raise ValueError("image_path or image_url is required for HeyGen Photo Avatar.")
    payload = {
        "type": "photo",
        "name": kwargs.pop("avatar_name", kwargs.pop("name", "easy-ai-clients Photo Avatar")),
        "file": image,
    }
    return _heygen.request_json(
        "POST",
        "/v3/avatars",
        payload=payload,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )


def _generate_photo_avatar_video(
    image_path=None,
    image_url=None,
    audio_path=None,
    audio_url=None,
    text=None,
    output_path=None,
    sync=True,
    **kwargs: Any,
):
    timeout_seconds = kwargs.get("timeout_seconds")
    explicit_audio = audio_fields(
        audio_path=audio_path,
        audio_url=audio_url,
        audio_asset_id=kwargs.pop("audio_asset_id", None),
        timeout_seconds=timeout_seconds,
    )
    if not explicit_audio and not text and not kwargs.get("script"):
        raise ValueError("HeyGen Photo Avatar requires audio, text, or script.")
    if explicit_audio and (text or kwargs.get("script")):
        raise ValueError("HeyGen Photo Avatar accepts either script or audio, not both.")

    avatar_raw = _create_photo_avatar(image_path, image_url, kwargs)
    avatar_id = _photo_avatar_id(avatar_raw)
    resolution = kwargs.pop("resolution", "720p")
    aspect_ratio = kwargs.pop("aspect_ratio", "9:16")
    base = {
        "type": "avatar",
        "avatar_id": avatar_id,
        "script": text or kwargs.pop("script", None),
        "voice_id": kwargs.pop("voice_id", kwargs.pop("voice", None)),
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "output_format": kwargs.pop("output_format", "mp4"),
        **explicit_audio,
    }
    payload = passthrough_payload(
        base,
        kwargs,
        exclude={"duration", "duration_seconds", "billing_duration_seconds"},
    )
    result = submit_video(
        payload,
        output_path=output_path,
        sync=sync,
        model=PHOTO_AVATAR_MODEL,
        kwargs=kwargs,
    )
    cost = _photo_avatar_cost({**kwargs, "resolution": resolution})
    result["cost_usd"] = cost["cost_usd"]
    result["cost_is_estimated"] = cost["cost_is_estimated"]
    result["cost_source"] = cost["cost_source"]
    result["avatar_id"] = avatar_id
    result["raw_response"]["photo_avatar"] = _heygen.clean_payload(avatar_raw)
    return result


def generate_avatar_video(
    avatar=None,
    image_path=None,
    image_url=None,
    audio_path=None,
    audio_url=None,
    text=None,
    output_path=None,
    sync=True,
    **kwargs: Any,
):
    model = _selected_model(kwargs)
    if model == PHOTO_AVATAR_MODEL and avatar is None:
        return _generate_photo_avatar_video(
            image_path=image_path,
            image_url=image_url,
            audio_path=audio_path,
            audio_url=audio_url,
            text=text,
            output_path=output_path,
            sync=sync,
            **kwargs,
        )

    timeout_seconds = kwargs.get("timeout_seconds")
    explicit_audio = audio_fields(
        audio_path=audio_path,
        audio_url=audio_url,
        audio_asset_id=kwargs.pop("audio_asset_id", None),
        timeout_seconds=timeout_seconds,
    )
    if avatar is not None:
        base = {
            "type": "avatar",
            "avatar_id": avatar,
            "script": text or kwargs.pop("script", None),
            "voice_id": kwargs.pop("voice_id", kwargs.pop("voice", None)),
            **explicit_audio,
        }
    else:
        base = {
            "type": "image",
            "image": media_union(
                image_path,
                image_url,
                kwargs.pop("image_asset_id", None),
                field_name="image",
                allow_base64=True,
            ),
            "script": text or kwargs.pop("script", None),
            "voice_id": kwargs.pop("voice_id", kwargs.pop("voice", None)),
            **explicit_audio,
        }
    payload = passthrough_payload(base, kwargs)
    if payload["type"] == "avatar" and not payload.get("avatar_id"):
        raise ValueError("avatar is required for HeyGen avatar video.")
    if payload["type"] == "image" and not payload.get("image"):
        raise ValueError("image_path or image_url is required when avatar is omitted.")
    if not payload.get("script") and not payload.get("audio_url") and not payload.get("audio_asset_id"):
        raise ValueError("HeyGen avatar_video requires text/script or audio.")
    return submit_video(
        payload,
        output_path=output_path,
        sync=sync,
        model=model,
        kwargs=kwargs,
    )


def get_generation_status(request_id, **kwargs):
    from ..._heygen_common import get_video

    return get_video(request_id, **kwargs)


def get_generation_result(request_id, output_path=None, **kwargs):
    from ..._heygen_common import build_video_result, cost_metadata, get_video

    raw = get_video(
        request_id,
        timeout_seconds=kwargs.get("timeout_seconds"),
        status_url=kwargs.get("status_url"),
        result_url=kwargs.get("result_url"),
        task_url=kwargs.get("task_url"),
        poll_url=kwargs.get("poll_url"),
    )
    return build_video_result(
        model=kwargs.get("model") or VIDEO_MODEL,
        raw_response=raw,
        request_id=request_id,
        output_path=output_path,
        cost=cost_metadata(kwargs),
    )


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        from ..._shared import download_file, normalize_output_path

        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
