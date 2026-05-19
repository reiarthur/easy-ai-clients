"""HeyGen v3 Video Agent adapter."""

from __future__ import annotations

from typing import Any

from .... import _heygen
from ..._heygen_common import AGENT_MODEL, build_video_result, cost_metadata, passthrough_payload


def generate_agent_video(prompt, output_path=None, sync=True, **kwargs: Any):
    payload = passthrough_payload({"prompt": str(prompt or "").strip()}, kwargs)
    if not payload.get("prompt"):
        raise ValueError("prompt is required.")
    raw = _heygen.request_json(
        "POST",
        "/v3/video-agents",
        payload=payload,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    session_id = _heygen.response_id(raw, "session_id")
    final_raw = raw
    if sync and session_id:
        final_raw = _heygen.wait_for_result(
            lambda: get_agent_session(session_id, timeout_seconds=60),
            timeout_seconds=kwargs.get("timeout_seconds"),
            poll_interval_seconds=kwargs.get("poll_interval_seconds"),
        )
        item = _heygen.data(final_raw)
        video_id = item.get("video_id") if isinstance(item, dict) else None
        if video_id:
            try:
                from ..._heygen_common import get_video

                final_raw = get_video(video_id, timeout_seconds=kwargs.get("timeout_seconds"))
            except Exception:
                pass
    return build_video_result(
        model=kwargs.get("model") or AGENT_MODEL,
        raw_response=final_raw,
        request_id=session_id,
        output_path=output_path,
        cost=cost_metadata(kwargs),
        extra={"session_id": session_id} if session_id else None,
    )


def get_agent_session(session_id, *, timeout_seconds=None, **kwargs):
    return _heygen.request_json(
        "GET",
        f"/v3/video-agents/{_heygen.quote_path(session_id)}",
        params=kwargs,
        timeout_seconds=timeout_seconds,
    )


def get_generation_status(request_id, **kwargs):
    return get_agent_session(request_id, **kwargs)


def get_generation_result(request_id, output_path=None, **kwargs):
    return generate_agent_video_result(request_id, output_path=output_path, **kwargs)


def generate_agent_video_result(request_id, output_path=None, **kwargs):
    raw = get_agent_session(request_id, timeout_seconds=kwargs.get("timeout_seconds"))
    item = _heygen.data(raw)
    video_id = item.get("video_id") if isinstance(item, dict) else None
    if video_id:
        try:
            from ..._heygen_common import get_video

            raw = get_video(video_id, timeout_seconds=kwargs.get("timeout_seconds"))
        except Exception:
            pass
    return build_video_result(
        model=kwargs.get("model") or AGENT_MODEL,
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
    return generate_agent_video_result(request_id, output_path=output_path, **kwargs)

