"""Runway video-to-video wrapper."""

from ..._shared import (
    download_file,
    normalize_output_path,
    normalize_runway_status,
    require_env,
    runway_get_task,
    runway_media_uri,
    runway_submit,
    runway_wait_for_task,
    validate_enum,
    validate_number,
)
from ..post_processing import build_result

PROVIDER = "runway"
ENV_NAME = "RUNWAYML_API_SECRET"
DEFAULT_MODEL = "gen4_aleph"
COST_SOURCE = "runway_api_pricing_credits_snapshot_2026-05-14"
CREDIT_TO_USD = 0.01

DOCUMENTED_MODEL_DATA = {
    DEFAULT_MODEL: {
        "credits_per_second": 15,
        "durations": "range",
        "default_duration": 5,
        "ratios": ["1280:720", "720:1280", "960:960", "1104:832", "832:1104", "1584:672"],
    },
}

COMMON_OPTIONS = {
    "model",
    "timeout_seconds",
    "poll_interval_seconds",
    "extra_payload",
    "duration",
    "duration_seconds",
    "billing_duration_seconds",
}


def _selected_model(kwargs):
    return kwargs.get("model", DEFAULT_MODEL)


def _duration(model, kwargs):
    if model not in DOCUMENTED_MODEL_DATA:
        return kwargs.get("billing_duration_seconds", kwargs.get("duration_seconds", kwargs.get("duration", 5)))
    value = kwargs.get(
        "billing_duration_seconds",
        kwargs.get("duration_seconds", kwargs.get("duration", DOCUMENTED_MODEL_DATA[model]["default_duration"])),
    )
    parsed = float(value)
    return int(parsed) if parsed.is_integer() else parsed


def _ratio(model, kwargs):
    ratio = kwargs.get("ratio")
    if ratio is None:
        return None
    validate_enum("ratio", ratio, DOCUMENTED_MODEL_DATA.get(model, {"ratios": []})["ratios"], PROVIDER, model)
    return ratio


def _build_payload(model, prepared, kwargs):
    validate_number("seed", kwargs.get("seed"), 0, 4294967295, PROVIDER, model)
    payload = {
        "model": model,
        "videoUri": prepared["video"],
    }
    if prepared["prompt"]:
        payload["promptText"] = prepared["prompt"]
    ratio = _ratio(model, kwargs)
    if ratio:
        payload["ratio"] = ratio
    if prepared["image"] or prepared["reference"]:
        if prepared["image"] and prepared["reference"]:
            raise ValueError("Runway gen4_aleph accepts at most one image/reference asset for video_to_video.")
        payload["references"] = [
            {"type": "image", "uri": value}
            for value in (prepared["image"], prepared["reference"])
            if value is not None
        ]
    if "seed" in kwargs and kwargs["seed"] is not None:
        payload["seed"] = kwargs["seed"]
    for name, value in kwargs.items():
        if name not in COMMON_OPTIONS and name not in payload and value is not None:
            payload[name] = value
    if "extra_payload" in kwargs:
        from ..._shared import merge_extra_payload

        payload = merge_extra_payload(payload, kwargs)
    return payload


def _cost(model, kwargs):
    if model not in DOCUMENTED_MODEL_DATA:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_credits": 0.0,
            "credit_source": "unavailable",
            "cost_reason": f"No documented pricing metadata is available for Runway model `{model}`.",
        }
    duration = _duration(model, kwargs)
    credits = DOCUMENTED_MODEL_DATA[model]["credits_per_second"] * duration
    return {
        "cost_usd": credits * CREDIT_TO_USD,
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_credits": credits,
        "credit_source": "Runway API credit pricing and published credit purchase rate",
        "cost_reason": "Runway task responses do not expose per-task credits; wrapper estimates from official credits per second and documented credit purchase rate.",
    }


def _task_id(raw):
    task_id = raw.get("id") or raw.get("taskId")
    if not task_id:
        raise RuntimeError("Runway submission did not return a task id.")
    return task_id


def _video_url(raw):
    output = raw.get("output") if isinstance(raw, dict) else None
    if isinstance(output, str):
        return output
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("url") or first.get("uri")
    return raw.get("video_url") if isinstance(raw, dict) else None


def generate_video_to_video(
    prompt=None,
    video_path=None,
    video_url=None,
    image_path=None,
    image_url=None,
    reference_path=None,
    reference_url=None,
    output_path=None,
    sync=True,
    **kwargs,
):
    model = _selected_model(kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    video = runway_media_uri(
        video_path,
        video_url,
        "video_path",
        "video_url",
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    if not video:
        raise ValueError("Runway video_to_video requires video_path or video_url.")
    image = runway_media_uri(
        image_path,
        image_url,
        "image_path",
        "image_url",
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    reference = runway_media_uri(
        reference_path,
        reference_url,
        "reference_path",
        "reference_url",
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    prepared = {
        "prompt": str(prompt).strip() if prompt is not None else None,
        "video": video,
        "image": image,
        "reference": reference,
        "output_path": normalize_output_path(output_path),
    }
    payload = _build_payload(model, prepared, kwargs)
    cost = _cost(model, kwargs)
    submission = runway_submit("/v1/video_to_video", payload, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    task_id = _task_id(submission)

    if not sync:
        extra = {"cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
        return build_result(PROVIDER, model, "submitted", task_id, None, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], submission, extra)

    raw = runway_wait_for_task(task_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"), poll_interval_seconds=kwargs.get("poll_interval_seconds"))
    video_url = _video_url(raw)
    if not video_url:
        raise RuntimeError(f"Runway video-to-video task {task_id} did not include an output video URL.")
    extra = {"cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model, "completed", task_id, video_url, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def get_generation_status(request_id, **kwargs):
    model = _selected_model(kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    raw = runway_get_task(request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    return {"provider": PROVIDER, "model": model, "request_id": request_id, "status": normalize_runway_status(raw.get("status")), "raw_response": raw}


def get_generation_result(request_id, output_path=None, **kwargs):
    model = _selected_model(kwargs)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    raw = runway_get_task(request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    status = normalize_runway_status(raw.get("status"))
    if status != "completed":
        raise RuntimeError(f"Runway task {request_id} is not complete. Current status: {status}.")
    video_url = _video_url(raw)
    if not video_url:
        raise RuntimeError(f"Runway video-to-video task {request_id} did not include an output video URL.")
    extra = {"cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
