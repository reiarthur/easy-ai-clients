"""HeyGen v3 image-to-video adapter."""

from __future__ import annotations

from typing import Any

from ..._heygen_common import VIDEO_MODEL, media_union, passthrough_payload, submit_video


def generate_image_to_video(prompt=None, image_path=None, image_url=None, output_path=None, sync=True, **kwargs: Any):
    payload = passthrough_payload(
        {
            "type": "image",
            "image": media_union(
                image_path,
                image_url,
                kwargs.pop("image_asset_id", None),
                field_name="image",
                allow_base64=True,
            ),
            "script": prompt or kwargs.pop("script", None),
            "voice_id": kwargs.pop("voice_id", kwargs.pop("voice", None)),
        },
        kwargs,
    )
    if not payload.get("image"):
        raise ValueError("image_path, image_url, or image_asset_id is required.")
    if not payload.get("script") and not payload.get("audio_url") and not payload.get("audio_asset_id"):
        raise ValueError("HeyGen image_to_video requires prompt/script or audio_url/audio_asset_id.")
    return submit_video(
        payload,
        output_path=output_path,
        sync=sync,
        model=kwargs.get("model") or VIDEO_MODEL,
        kwargs=kwargs,
    )


def get_generation_status(request_id, **kwargs):
    from ..._avatar_video._apis.heygen import get_generation_status as _get_generation_status

    return _get_generation_status(request_id, **kwargs)


def get_generation_result(request_id, output_path=None, **kwargs):
    from ..._avatar_video._apis.heygen import get_generation_result as _get_generation_result

    return _get_generation_result(request_id, output_path=output_path, **kwargs)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    from ..._avatar_video._apis.heygen import download_generation as _download_generation

    return _download_generation(
        request_id=request_id,
        video_url=video_url,
        output_path=output_path,
        **kwargs,
    )
