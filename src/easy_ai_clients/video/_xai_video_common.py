"""Shared xAI Imagine video helpers."""

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
    normalize_result,
    require_env,
    safe_provider_url,
)

PROVIDER = "xai"
ENV_NAME = "XAI_API_KEY"
BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-imagine-video"
COST_SOURCE = "xai_imagine_pricing_2026-05"


def headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def submit(endpoint: str, payload: Mapping[str, Any], timeout_seconds: float | None = None) -> dict[str, Any]:
    api_key = require_env(ENV_NAME, "xAI")
    return http_json("POST", f"{BASE_URL}{endpoint}", headers=headers(api_key), payload=dict(payload), timeout_seconds=timeout_seconds)


def video_endpoint_url(request_id: str) -> str:
    return f"{BASE_URL}/videos/{urllib.parse.quote(str(request_id), safe='')}"


def async_refs(raw: Mapping[str, Any] | None, request_id_value: str | None) -> dict[str, Any]:
    refs = merge_async_refs(None, raw or {})
    if request_id_value and not any(
        refs.get(key) for key in ("status_url", "poll_url", "task_url", "result_url")
    ):
        return merge_async_refs(refs, task_url=video_endpoint_url(request_id_value))
    return refs


def get_video(
    request_id: str,
    timeout_seconds: float | None = None,
    status_url: str | None = None,
    result_url: str | None = None,
    task_url: str | None = None,
    poll_url: str | None = None,
) -> dict[str, Any]:
    api_key = require_env(ENV_NAME, "xAI")
    url = (
        safe_provider_url(status_url)
        or safe_provider_url(result_url)
        or safe_provider_url(task_url)
        or safe_provider_url(poll_url)
        or video_endpoint_url(request_id)
    )
    return http_json("GET", url, headers=headers(api_key), timeout_seconds=timeout_seconds)


def status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "done":
        return "completed"
    if normalized in {"pending", "queued"}:
        return "queued"
    if normalized in {"running", "processing"}:
        return "running"
    if normalized in {"expired", "failed"}:
        return "failed"
    return normalized or "submitted"


def wait(
    request_id: str,
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
            request_id,
            timeout_seconds=60,
            status_url=status_url,
            result_url=result_url,
            task_url=task_url,
            poll_url=poll_url,
        )
        current = status(last.get("status"))
        if current == "completed":
            return last
        if current == "failed":
            raise RuntimeError(f"xAI video request {request_id} ended with status {last}.")
        time.sleep(max(1, interval))
    raise TimeoutError(f"xAI video request {request_id} timed out. Last status: {last}")


def request_id(raw: Mapping[str, Any]) -> str | None:
    value = raw.get("request_id") or raw.get("id")
    return str(value) if value else None


def cost(model: str, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    duration = float(kwargs.get("duration", kwargs.get("duration_seconds", 5)) or 5)
    resolution = str(kwargs.get("resolution") or "480p").lower()
    price_per_second = 0.07 if resolution == "720p" else 0.05
    return {
        "cost_usd": round(duration * price_per_second, 6),
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_details": {
            "duration_seconds": duration,
            "resolution": resolution,
            "usd_per_second": price_per_second,
            "model": model,
        },
    }


def payload(model: str, prompt: Any, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    body = {"model": model}
    if prompt is not None and str(prompt).strip():
        body["prompt"] = clean_text(prompt, "prompt")
    for key, value in kwargs.items():
        if key not in {"sync", "timeout_seconds", "poll_interval_seconds", "output_path"} and value is not None:
            body[key] = value
    return body


def finalize(
    *,
    endpoint: str,
    model: str,
    payload_value: Mapping[str, Any],
    output_path: str | None,
    sync: bool,
    timeout_seconds: float | None,
    poll_interval_seconds: float | None,
) -> dict[str, Any]:
    pricing = cost(model, payload_value)
    raw = submit(endpoint, payload_value, timeout_seconds=timeout_seconds)
    rid = request_id(raw)
    refs = async_refs(raw, rid)
    if not sync:
        return normalize_result(
            PROVIDER,
            model,
            "submitted",
            rid,
            None,
            normalize_output_path(output_path),
            pricing["cost_usd"],
            pricing["cost_is_estimated"],
            pricing["cost_source"],
            raw,
            {**refs, "cost_details": pricing["cost_details"]},
        )
    final = wait(
        rid,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        status_url=refs.get("status_url"),
        result_url=refs.get("result_url"),
        task_url=refs.get("task_url"),
        poll_url=refs.get("poll_url"),
    )
    video_url = extract_video_url(final)
    saved = download_file(video_url, normalize_output_path(output_path)) if video_url and output_path else normalize_output_path(output_path)
    refs = merge_async_refs(refs, final)
    return normalize_result(
        PROVIDER,
        model,
        "completed",
        rid,
        video_url,
        saved,
        pricing["cost_usd"],
        pricing["cost_is_estimated"],
        pricing["cost_source"],
        {"submission": raw, "result": final},
        {**refs, "cost_details": pricing["cost_details"]},
    )


def media_object(path: str | None, url: str | None, path_name: str, url_name: str) -> dict[str, str] | None:
    value = media_reference(path, url, path_name, url_name)
    return {"url": value} if value else None


__all__ = [
    "DEFAULT_MODEL",
    "PROVIDER",
    "async_refs",
    "cost",
    "finalize",
    "get_video",
    "media_object",
    "payload",
    "status",
]
