"""Shared Together AI video helpers."""

from __future__ import annotations

import time
import urllib.parse
from collections.abc import Mapping
from typing import Any

from ._shared import (
    clean_text,
    download_file,
    extract_video_url,
    http_json,
    media_reference,
    merge_async_refs,
    normalize_output_path,
    require_env,
    safe_provider_url,
)

PROVIDER = "together"
ENV_NAME = "TOGETHER_API_KEY"
BASE_URL = "https://api.together.xyz/v1"


def headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def submit_video(payload: Mapping[str, Any], *, timeout_seconds: float | None = None) -> dict[str, Any]:
    api_key = require_env(ENV_NAME, "Together")
    return http_json(
        "POST",
        f"{BASE_URL}/videos",
        headers=headers(api_key),
        payload=dict(payload),
        timeout_seconds=timeout_seconds,
    )


def video_endpoint_url(video_id: str) -> str:
    return f"{BASE_URL}/videos/{urllib.parse.quote(str(video_id), safe='')}"


def async_refs(raw: Mapping[str, Any] | None, video_id: str | None) -> dict[str, Any]:
    refs = merge_async_refs(None, raw or {})
    if video_id and not any(
        refs.get(key) for key in ("status_url", "poll_url", "task_url", "result_url")
    ):
        return merge_async_refs(refs, task_url=video_endpoint_url(video_id))
    return refs


def get_video(
    video_id: str,
    *,
    timeout_seconds: float | None = None,
    status_url: str | None = None,
    result_url: str | None = None,
    task_url: str | None = None,
    poll_url: str | None = None,
) -> dict[str, Any]:
    api_key = require_env(ENV_NAME, "Together")
    url = (
        safe_provider_url(status_url)
        or safe_provider_url(result_url)
        or safe_provider_url(task_url)
        or safe_provider_url(poll_url)
        or video_endpoint_url(video_id)
    )
    return http_json(
        "GET",
        url,
        headers=headers(api_key),
        timeout_seconds=timeout_seconds,
    )


def normalize_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    if status in {"completed", "complete", "succeeded", "success"}:
        return "completed"
    if status in {"running", "processing", "in_progress"}:
        return "running"
    if status in {"queued", "pending"}:
        return "queued"
    if status in {"failed", "error"}:
        return "failed"
    if status in {"cancelled", "canceled"}:
        return "canceled"
    return "submitted"


def wait_for_video(
    video_id: str,
    *,
    timeout_seconds: float | None = None,
    poll_interval_seconds: float | None = None,
    status_url: str | None = None,
    result_url: str | None = None,
    task_url: str | None = None,
    poll_url: str | None = None,
) -> dict[str, Any]:
    deadline = time.monotonic() + float(timeout_seconds or 900)
    interval = float(poll_interval_seconds or 5)
    last = {}
    while time.monotonic() < deadline:
        last = get_video(
            video_id,
            timeout_seconds=60,
            status_url=status_url,
            result_url=result_url,
            task_url=task_url,
            poll_url=poll_url,
        )
        status = normalize_status(last.get("status"))
        if status == "completed":
            return last
        if status in {"failed", "canceled"}:
            raise RuntimeError(f"Together video {video_id} ended with status {last}.")
        time.sleep(max(1, interval))
    raise TimeoutError(f"Together video {video_id} timed out. Last status: {last}")


def request_id(raw: Mapping[str, Any]) -> str | None:
    for key in ("id", "video_id", "request_id", "job_id"):
        if raw.get(key):
            return str(raw[key])
    data = raw.get("data")
    if isinstance(data, Mapping):
        return request_id(data)
    return None


def cost(model: str, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cost_usd": 0.0,
        "cost_is_estimated": False,
        "cost_source": "unavailable",
        "cost_details": {"model": model},
        "cost_reason": (
            "Together video responses and public docs do not expose a stable "
            "provider-independent USD cost for this generic wrapper."
        ),
    }


def common_payload(model: str, prompt: Any, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    payload = {"model": model}
    if prompt is not None and str(prompt).strip():
        payload["prompt"] = clean_text(prompt, "prompt")
    for key, value in kwargs.items():
        if key not in {"sync", "timeout_seconds", "poll_interval_seconds", "output_path"} and value is not None:
            payload[key] = value
    return payload


def build_result(
    *,
    model: str,
    status: str,
    request_id_value: str | None,
    video_url: str | None,
    output_path: str | None,
    raw: Mapping[str, Any],
    cost_metadata: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from ._shared import normalize_result

    return normalize_result(
        PROVIDER,
        model,
        status,
        request_id_value,
        video_url,
        output_path,
        cost_metadata["cost_usd"],
        cost_metadata["cost_is_estimated"],
        cost_metadata["cost_source"],
        raw,
        {
            "cost_reason": cost_metadata["cost_reason"],
            "cost_details": cost_metadata["cost_details"],
            **dict(extra or {}),
        },
    )


def finalize_or_submit(
    *,
    model: str,
    payload: Mapping[str, Any],
    output_path: str | None,
    sync: bool,
    timeout_seconds: float | None,
    poll_interval_seconds: float | None,
) -> dict[str, Any]:
    cost_metadata = cost(model, payload)
    raw = submit_video(payload, timeout_seconds=timeout_seconds)
    video_id = request_id(raw)
    refs = async_refs(raw, video_id)
    if not sync:
        return build_result(
            model=model,
            status="submitted",
            request_id_value=video_id,
            video_url=None,
            output_path=normalize_output_path(output_path),
            raw=raw,
            cost_metadata=cost_metadata,
            extra=refs,
        )
    final = wait_for_video(
        video_id,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        status_url=refs.get("status_url"),
        result_url=refs.get("result_url"),
        task_url=refs.get("task_url"),
        poll_url=refs.get("poll_url"),
    )
    video_url = extract_video_url(final)
    saved_path = download_file(video_url, normalize_output_path(output_path)) if video_url and output_path else normalize_output_path(output_path)
    refs = merge_async_refs(refs, final)
    return build_result(
        model=model,
        status="completed",
        request_id_value=video_id,
        video_url=video_url,
        output_path=saved_path,
        raw={"submission": raw, "result": final},
        cost_metadata=cost_metadata,
        extra=refs,
    )


def media(path: str | None, url: str | None, path_name: str, url_name: str) -> str | None:
    return media_reference(path, url, path_name, url_name)


__all__ = [
    "PROVIDER",
    "build_result",
    "common_payload",
    "finalize_or_submit",
    "get_video",
    "async_refs",
    "media",
    "normalize_status",
    "request_id",
]
