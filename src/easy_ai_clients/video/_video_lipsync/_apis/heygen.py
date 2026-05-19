"""HeyGen v3 video lip-sync adapter."""

from __future__ import annotations

from typing import Any

from ..._heygen_common import media_union, passthrough_payload, submit_lipsync


def generate_video_lipsync(video_path=None, video_url=None, audio_path=None, audio_url=None, text=None, output_path=None, sync=True, **kwargs: Any):
    if text and not audio_path and not audio_url and not kwargs.get("audio_asset_id"):
        raise ValueError("HeyGen video_lipsync requires audio; synthesize text first or pass audio.")
    payload = passthrough_payload(
        {
            "video": media_union(
                video_path,
                video_url,
                kwargs.pop("video_asset_id", None),
                field_name="video",
            ),
            "audio": media_union(
                audio_path,
                audio_url,
                kwargs.pop("audio_asset_id", None),
                field_name="audio",
            ),
        },
        kwargs,
    )
    if not payload.get("video"):
        raise ValueError("video_path, video_url, or video_asset_id is required.")
    if not payload.get("audio"):
        raise ValueError("audio_path, audio_url, or audio_asset_id is required.")
    return submit_lipsync(payload, output_path=output_path, sync=sync, kwargs=kwargs)


def get_generation_status(request_id, **kwargs):
    from ..._heygen_common import get_lipsync

    return get_lipsync(request_id, **kwargs)


def get_generation_result(request_id, output_path=None, **kwargs):
    from ..._heygen_common import LIPSYNC_MODEL, build_video_result, cost_metadata, get_lipsync

    raw = get_lipsync(request_id, timeout_seconds=kwargs.get("timeout_seconds"))
    return build_video_result(
        model=kwargs.get("model") or LIPSYNC_MODEL,
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
