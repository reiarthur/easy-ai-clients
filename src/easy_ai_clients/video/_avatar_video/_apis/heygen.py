"""HeyGen v3 avatar-video adapter."""

from __future__ import annotations

from typing import Any

from ..._heygen_common import (
    VIDEO_MODEL,
    audio_fields,
    media_union,
    passthrough_payload,
    submit_video,
)


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
        model=kwargs.get("model") or VIDEO_MODEL,
        kwargs=kwargs,
    )


def get_generation_status(request_id, **kwargs):
    from ..._heygen_common import get_video

    return get_video(request_id, **kwargs)


def get_generation_result(request_id, output_path=None, **kwargs):
    from ..._heygen_common import build_video_result, cost_metadata, get_video

    raw = get_video(request_id, timeout_seconds=kwargs.get("timeout_seconds"))
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
