"""Runway text-to-video wrapper."""

from ..._shared import (
    download_file,
    normalize_output_path,
    normalize_runway_status,
    require_env,
    runway_get_task,
    runway_submit,
    runway_wait_for_task,
    validate_allowed_kwargs,
    validate_enum,
    validate_number,
)
from ..post_processing import build_result
from ..pre_processing import prepare_text_to_video

PROVIDER = "runway"
ENV_NAME = "RUNWAYML_API_SECRET"
DEFAULT_MODEL = "veo3.1_fast"
COST_SOURCE = "runway_api_pricing_credits_snapshot_2026-05-13"
CREDIT_TO_USD = 0.01

DOCUMENTED_MODEL_DATA = {
    "gen4.5": {"credits_per_second": 12, "durations": "range", "default_duration": 5, "ratios": ["1280:720", "720:1280"], "supports_seed": True, "supports_audio": False},
    "veo3": {"credits_per_second": 40, "durations": [8], "default_duration": 8, "ratios": ["1280:720", "720:1280", "1080:1920", "1920:1080"], "supports_seed": False, "supports_audio": False},
    "veo3.1": {"credits_per_second": 20, "audio_credits_per_second": 40, "durations": [4, 6, 8], "default_duration": 4, "ratios": ["1280:720", "720:1280", "1080:1920", "1920:1080"], "supports_seed": False, "supports_audio": True},
    "veo3.1_fast": {"credits_per_second": 10, "audio_credits_per_second": 15, "durations": [4, 6, 8], "default_duration": 4, "ratios": ["1280:720", "720:1280", "1080:1920", "1920:1080"], "supports_seed": False, "supports_audio": True},
}

DOCUMENTED_MODEL_OPTIONS = {
    name: {"ratio", "duration", "seed", "audio", "content_moderation", "public_figure_threshold"}
    for name in DOCUMENTED_MODEL_DATA
}

COMMON_OPTIONS = {"model", "timeout_seconds", "poll_interval_seconds", "extra_payload"}


def _selected_model(kwargs):
    return kwargs.get("model", DEFAULT_MODEL)


def _duration(model, kwargs):
    if model not in DOCUMENTED_MODEL_DATA:
        return kwargs.get("duration", 5)
    value = kwargs.get("duration", DOCUMENTED_MODEL_DATA[model]["default_duration"])
    if DOCUMENTED_MODEL_DATA[model]["durations"] == "range":
        parsed = float(value)
        return int(parsed) if parsed.is_integer() else parsed
    parsed = int(value)
    return parsed


def _ratio(model, kwargs):
    ratio = kwargs.get("ratio", DOCUMENTED_MODEL_DATA.get(model, {"ratios": ["1280:720"]})["ratios"][0])
    validate_enum("ratio", ratio, DOCUMENTED_MODEL_DATA.get(model, {"ratios": []})["ratios"], PROVIDER, model)
    return ratio


def _content_moderation(model, kwargs):
    if kwargs.get("content_moderation") is not None:
        return kwargs.get("content_moderation")
    threshold = kwargs.get("public_figure_threshold")
    if threshold is None:
        return None
    validate_enum("public_figure_threshold", threshold, ["auto", "low"], PROVIDER, model)
    return {"publicFigureThreshold": threshold}


def _audio(model, kwargs):
    if model in DOCUMENTED_MODEL_DATA and not DOCUMENTED_MODEL_DATA[model]["supports_audio"]:
        return None
    return bool(kwargs.get("audio", False))


def _build_payload(model, prepared, kwargs):
    validate_allowed_kwargs(kwargs, DOCUMENTED_MODEL_OPTIONS.get(model, set()), model, PROVIDER, "text_to_video", COMMON_OPTIONS)
    validate_number("seed", kwargs.get("seed"), 0, 4294967295, PROVIDER, model)
    payload = {
        "model": model,
        "promptText": prepared["prompt"],
        "ratio": _ratio(model, kwargs),
        "duration": _duration(model, kwargs),
    }
    if "seed" in kwargs and kwargs["seed"] is not None:
        payload["seed"] = kwargs["seed"]
    audio = _audio(model, kwargs)
    if audio is not None:
        payload["audio"] = audio
    moderation = _content_moderation(model, kwargs)
    if moderation is not None:
        payload["contentModeration"] = moderation
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
    audio = bool(_audio(model, kwargs))
    credits_per_second = DOCUMENTED_MODEL_DATA[model].get("audio_credits_per_second") if audio else DOCUMENTED_MODEL_DATA[model]["credits_per_second"]
    credits = credits_per_second * duration
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


def generate_text_to_video(prompt, output_path=None, sync=True, **kwargs):
    model = _selected_model(kwargs)
    prepared = prepare_text_to_video(prompt, output_path)
    payload = _build_payload(model, prepared, kwargs)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    submission = runway_submit("/v1/text_to_video", payload, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    task_id = _task_id(submission)

    if not sync:
        extra = {"cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
        return build_result(PROVIDER, model, "submitted", task_id, None, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], submission, extra)

    raw = runway_wait_for_task(task_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"), poll_interval_seconds=kwargs.get("poll_interval_seconds"))
    video_url = _video_url(raw)
    if not video_url:
        raise RuntimeError(f"Runway text-to-video task {task_id} did not include an output video URL.")
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
        raise RuntimeError(f"Runway text-to-video task {request_id} did not include an output video URL.")
    extra = {"cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
