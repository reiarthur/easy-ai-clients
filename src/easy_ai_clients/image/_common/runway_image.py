"""Shared Runway image operation helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...video._shared import (
    extract_video_url,
    require_env,
    runway_media_uri,
    runway_submit,
    runway_wait_for_task,
)
from .http_utils import download_bytes
from .provider_utils import image_bytes_to_base64_png, image_result


def submit_runway_image_task(
    *,
    endpoint: str,
    payload: Mapping[str, Any],
    model: str,
    prompt: str,
    sync: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    api_key = require_env("RUNWAYML_API_SECRET", "Runway")
    raw = runway_submit(endpoint, dict(payload), api_key, timeout_seconds=timeout_seconds)
    request_id = raw.get("id") or raw.get("task_id") or raw.get("request_id")
    if not sync:
        return image_result(
            warnings="Runway image task was submitted asynchronously; call the provider task API for the final image.",
            request_id=str(request_id or ""),
            cost_source="unavailable",
            cost_is_estimated=False,
            cost_details={"model": model, "prompt": prompt, "raw_response": raw},
        )
    final = runway_wait_for_task(request_id, api_key, timeout_seconds=timeout_seconds)
    image_url = extract_video_url(final) or extract_video_url(raw)
    if not image_url:
        return image_result(
            warnings=f"Runway image task {request_id} did not return an image URL.",
            request_id=str(request_id or ""),
            cost_source="unavailable",
            cost_is_estimated=False,
            cost_details={"model": model, "raw_response": final},
        )
    return image_result(
        base64_value=image_bytes_to_base64_png(download_bytes(image_url, timeout_seconds=int(timeout_seconds))),
        request_id=str(request_id or ""),
        cost_source="unavailable",
        cost_is_estimated=False,
        cost_details={"model": model, "raw_response": final},
    )


def runway_uri(path: str | None, url: str | None, *, path_name: str, url_name: str, timeout_seconds: float) -> str | None:
    api_key = require_env("RUNWAYML_API_SECRET", "Runway")
    return runway_media_uri(path, url, path_name, url_name, api_key, timeout_seconds=timeout_seconds)


__all__ = ["runway_uri", "submit_runway_image_task"]
