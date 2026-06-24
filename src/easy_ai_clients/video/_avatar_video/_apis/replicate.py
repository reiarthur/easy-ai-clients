"""Replicate avatar-video wrapper."""

import time
import urllib.parse

from ..._shared import (
    extract_video_url,
    http_json,
    merge_async_refs,
    normalize_output_path,
    require_env,
    safe_async_refs,
    safe_provider_url,
)
from ..post_processing import build_result
from ..pre_processing import prepare_avatar_video

PROVIDER = "replicate"
ENV_NAME = "REPLICATE_API_TOKEN"
BASE_URL = "https://api.replicate.com"
DEFAULT_MODEL = "prunaai/p-video-avatar"
MODEL_ALIASES = {
    "replicate_prunaai_p_video_avatar": DEFAULT_MODEL,
    DEFAULT_MODEL: DEFAULT_MODEL,
}
COST_SOURCE = "replicate_prunaai_p_video_avatar_pricing_snapshot_2026-06-24"
TERMINAL_FAILURE_STATUSES = {"failed", "canceled", "cancelled", "aborted"}
COMMON_OPTIONS = {
    "model",
    "timeout_seconds",
    "poll_interval_seconds",
    "extra_payload",
    "billing_duration_seconds",
    "duration_seconds",
    "duration",
    "billing_cost_usd",
    "estimated_cost_usd",
    "cancel_after",
    "prompt",
}


def _selected_model(kwargs):
    selected = kwargs.get("model", DEFAULT_MODEL)
    return MODEL_ALIASES.get(str(selected).strip(), selected)


def _headers(api_key, sync):
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    if sync:
        headers["Prefer"] = "wait=5"
    return headers


def _prediction_url(prediction_id):
    return BASE_URL + "/v1/predictions/" + urllib.parse.quote(str(prediction_id), safe="")


def _prediction_endpoint(model):
    if model != DEFAULT_MODEL:
        raise ValueError("Replicate avatar_video only supports prunaai/p-video-avatar.")
    owner, name = model.split("/", 1)
    return BASE_URL + f"/v1/models/{owner}/{name}/predictions"


def _build_payload(model, prepared, kwargs):
    if model != DEFAULT_MODEL:
        raise ValueError("Replicate avatar_video only supports prunaai/p-video-avatar.")
    if not prepared["image"]:
        raise ValueError("Replicate avatar_video requires image/image_path/image_url.")
    if not prepared["audio"]:
        raise ValueError("Replicate avatar_video requires audio/audio_path/audio_url.")
    inputs = {
        "image": prepared["image"],
        "audio": prepared["audio"],
        "resolution": kwargs.get("resolution", "720p"),
        "video_prompt": kwargs.get("video_prompt", kwargs.get("prompt", "The person is talking.")),
    }
    if kwargs.get("negative_prompt"):
        inputs["negative_prompt"] = kwargs["negative_prompt"]
    for name, value in kwargs.items():
        if name not in COMMON_OPTIONS and name not in inputs and value is not None:
            inputs[name] = value
    payload = {"input": inputs}
    extra_payload = kwargs.get("extra_payload")
    if extra_payload is not None:
        if not isinstance(extra_payload, dict):
            raise ValueError("extra_payload must be a dictionary when provided.")
        payload.update(extra_payload)
    return payload


def _cost(kwargs):
    value = kwargs.get("billing_cost_usd", kwargs.get("estimated_cost_usd"))
    if value is not None:
        return {
            "cost_usd": float(value),
            "cost_is_estimated": True,
            "cost_source": "caller_estimate",
            "cost_reason": "Caller supplied estimated_cost_usd or billing_cost_usd.",
        }
    duration = kwargs.get("billing_duration_seconds", kwargs.get("duration_seconds", kwargs.get("duration")))
    if duration is None:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_reason": "Replicate pricing is documented per second, but duration was not supplied.",
        }
    resolution = kwargs.get("resolution", "720p")
    rates = {"720p": 0.025, "1080p": 0.045}
    if resolution not in rates:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_reason": "Replicate pricing is available only for 720p and 1080p.",
        }
    return {
        "cost_usd": float(duration) * rates[resolution],
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_reason": "Replicate pricing is estimated from documented per-second pricing by resolution.",
    }


def _request_id(prediction):
    prediction_id = prediction.get("id")
    if not prediction_id:
        raise RuntimeError("Replicate prediction did not return an id.")
    return prediction_id


def _async_refs(prediction, prediction_id):
    urls = prediction.get("urls") if isinstance(prediction, dict) else {}
    get_url = urls.get("get") if isinstance(urls, dict) else None
    cancel_url = urls.get("cancel") if isinstance(urls, dict) else None
    return safe_async_refs(
        prediction,
        task_url=get_url or _prediction_url(prediction_id),
        status_url=get_url,
        result_url=get_url,
        cancel_url=cancel_url,
        prediction_id=prediction_id,
    )


def _normalize_status(value):
    status = str(value or "").lower()
    if status in {"succeeded", "successful"}:
        return "completed"
    if status == "starting":
        return "queued"
    if status == "processing":
        return "running"
    if status in {"canceled", "cancelled"}:
        return "canceled"
    if status in {"failed", "aborted"}:
        return "failed"
    return "submitted"


def _get_prediction(request_id, api_key, kwargs):
    refs = merge_async_refs(None, kwargs, **_async_refs({}, request_id))
    url = (
        safe_provider_url(refs.get("status_url"))
        or safe_provider_url(refs.get("result_url"))
        or safe_provider_url(refs.get("task_url"))
        or _prediction_url(request_id)
    )
    raw = http_json(
        "GET",
        url,
        headers=_headers(api_key, False),
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    refs = merge_async_refs(refs, raw, **_async_refs(raw, request_id))
    return raw, refs


def _wait_for_result(request_id, api_key, kwargs):
    deadline = time.monotonic() + float(kwargs.get("timeout_seconds") or 900)
    interval = float(kwargs.get("poll_interval_seconds") or 5)
    last = {}
    while time.monotonic() < deadline:
        last, refs = _get_prediction(request_id, api_key, kwargs)
        status = str(last.get("status") or "").lower()
        if status in {"succeeded", "successful"}:
            return last, refs
        if status in TERMINAL_FAILURE_STATUSES:
            raise RuntimeError(f"Replicate prediction {request_id} ended with status {last}.")
        time.sleep(max(0.5, interval))
    raise TimeoutError(f"Replicate prediction {request_id} timed out. Last status: {last}")


def generate_avatar_video(
    image_path=None,
    image_url=None,
    audio_path=None,
    audio_url=None,
    text=None,
    output_path=None,
    sync=True,
    **kwargs,
):
    model = _selected_model(kwargs)
    prepared = prepare_avatar_video(image_path, image_url, audio_path, audio_url, text, output_path)
    payload = _build_payload(model, prepared, kwargs)
    cost = _cost(kwargs)
    api_key = require_env(ENV_NAME, "Replicate")
    headers = _headers(api_key, sync)
    if kwargs.get("cancel_after"):
        headers["Cancel-After"] = str(kwargs["cancel_after"])
    prediction = http_json(
        "POST",
        _prediction_endpoint(model),
        headers=headers,
        payload=payload,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    request_id = _request_id(prediction)
    refs = _async_refs(prediction, request_id)
    status = _normalize_status(prediction.get("status"))

    if not sync:
        return build_result(
            PROVIDER,
            model,
            status,
            request_id,
            extract_video_url(prediction),
            prepared["output_path"],
            cost["cost_usd"],
            cost["cost_is_estimated"],
            cost["cost_source"],
            prediction,
            {**refs, "cost_reason": cost["cost_reason"]},
        )

    video_url = extract_video_url(prediction)
    if status != "completed" or not video_url:
        final_prediction, refs = _wait_for_result(request_id, api_key, kwargs)
        video_url = extract_video_url(final_prediction)
        prediction = {"submission": prediction, "result": final_prediction}
    if not video_url:
        raise RuntimeError(f"Replicate prediction {request_id} did not include a video URL.")
    return build_result(
        PROVIDER,
        model,
        "completed",
        request_id,
        video_url,
        prepared["output_path"],
        cost["cost_usd"],
        cost["cost_is_estimated"],
        cost["cost_source"],
        prediction,
        {**refs, "cost_reason": cost["cost_reason"]},
    )


def get_generation_status(request_id, **kwargs):
    model = _selected_model(kwargs)
    api_key = require_env(ENV_NAME, "Replicate")
    raw, refs = _get_prediction(request_id, api_key, kwargs)
    return {
        "provider": PROVIDER,
        "model": model,
        "request_id": request_id,
        "status": _normalize_status(raw.get("status")),
        "raw_response": raw,
        **refs,
    }


def get_generation_result(request_id, output_path=None, **kwargs):
    model = _selected_model(kwargs)
    cost = _cost(kwargs)
    api_key = require_env(ENV_NAME, "Replicate")
    raw, refs = _get_prediction(request_id, api_key, kwargs)
    video_url = extract_video_url(raw)
    if not video_url:
        raise RuntimeError(f"Replicate prediction {request_id} did not include a video URL.")
    return build_result(
        PROVIDER,
        model,
        "completed",
        request_id,
        video_url,
        normalize_output_path(output_path),
        cost["cost_usd"],
        cost["cost_is_estimated"],
        cost["cost_source"],
        raw,
        {**refs, "cost_reason": cost["cost_reason"]},
    )


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        from ..._shared import download_file

        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
