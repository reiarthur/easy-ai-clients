"""Runway video-with-audio wrapper."""

from ..._shared import (
    download_file,
    extract_video_url,
    normalize_output_path,
    normalize_result,
    normalize_runway_status,
    require_env,
    runway_get_task,
    runway_media_uri,
    runway_submit,
    runway_wait_for_task,
)

PROVIDER = "runway"
ENV_NAME = "RUNWAYML_API_SECRET"
DEFAULT_MODEL = "eleven_multilingual_v2"
API_ENDPOINT = "/v1/video_to_audio"
CREDIT_TO_USD = 0.01


def _cost(model, kwargs):
    duration = float(kwargs.get("duration", kwargs.get("duration_seconds", 0)) or 0)
    credits = duration if duration > 0 else 2.0
    return {
        "cost_usd": round(credits * CREDIT_TO_USD, 6),
        "cost_is_estimated": True,
        "cost_source": "runway_api_pricing_credits_snapshot_2026-05",
        "cost_details": {"credits": credits, "model": model},
    }


def generate_video_with_audio(video_path=None, video_url=None, prompt=None, output_path=None, sync=True, **kwargs):
    model = kwargs.pop("model", DEFAULT_MODEL)
    api_key = require_env(ENV_NAME, "Runway")
    video = runway_media_uri(video_path, video_url, "video_path", "video_url", api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    if not video:
        raise ValueError("Runway video_with_audio requires video_path or video_url.")
    payload = {"model": model, "videoUri": video}
    if prompt:
        payload["promptText"] = str(prompt).strip()
    payload.update({key: value for key, value in kwargs.items() if value is not None})
    cost = _cost(model, kwargs)
    raw = runway_submit(API_ENDPOINT, payload, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    task_id = raw.get("id") or raw.get("taskId")
    if not sync:
        return normalize_result(PROVIDER, model, "submitted", task_id, None, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, {"cost_details": cost["cost_details"]})
    final = runway_wait_for_task(task_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"), poll_interval_seconds=kwargs.get("poll_interval_seconds"))
    url = extract_video_url(final)
    saved = download_file(url, normalize_output_path(output_path)) if url and output_path else normalize_output_path(output_path)
    return normalize_result(PROVIDER, model, "completed", task_id, url, saved, cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], final, {"cost_details": cost["cost_details"]})


def get_generation_status(request_id, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    api_key = require_env(ENV_NAME, "Runway")
    raw = runway_get_task(request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    return {"provider": PROVIDER, "model": model, "request_id": request_id, "status": normalize_runway_status(raw.get("status")), "raw_response": raw}


def get_generation_result(request_id, output_path=None, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    raw = runway_get_task(request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    url = extract_video_url(raw)
    return normalize_result(PROVIDER, model, normalize_runway_status(raw.get("status")), request_id, url, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, {"cost_details": cost["cost_details"]})


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    return get_generation_result(request_id, output_path=output_path, **kwargs)


__all__ = ["API_ENDPOINT", "DEFAULT_MODEL", "download_generation", "generate_video_with_audio", "get_generation_result", "get_generation_status"]
