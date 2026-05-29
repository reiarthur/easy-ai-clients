"""Runway motion-control wrapper for Act-Two character performance."""

from ..._shared import (
    download_file,
    merge_async_refs,
    normalize_output_path,
    normalize_runway_status,
    require_env,
    runway_async_refs,
    runway_get_task,
    runway_submit,
    runway_wait_for_task,
    validate_allowed_kwargs,
    validate_enum,
    validate_number,
)
from ..post_processing import build_result
from ..pre_processing import prepare_motion_control

PROVIDER = "runway"
ENV_NAME = "RUNWAYML_API_SECRET"
DEFAULT_MODEL = "act_two"
COST_SOURCE = "runway_api_pricing_credits_snapshot_2026-05-13"
CREDIT_TO_USD = 0.01

DOCUMENTED_MODEL_OPTIONS = {
    DEFAULT_MODEL: {
        "duration_seconds",
        "billing_duration_seconds",
        "body_control",
        "bodyControl",
        "expression_intensity",
        "expressionIntensity",
        "ratio",
        "seed",
        "content_moderation",
        "public_figure_threshold",
    }
}

COMMON_OPTIONS = {"model", "timeout_seconds", "poll_interval_seconds", "extra_payload"}
RATIOS = ["1280:720", "720:1280", "960:960", "1104:832", "832:1104", "1584:672"]


def _selected_model(kwargs):
    return kwargs.get("model", DEFAULT_MODEL)


def _duration(kwargs):
    if kwargs.get("billing_duration_seconds") is not None:
        value = float(kwargs.get("billing_duration_seconds"))
    elif kwargs.get("duration_seconds") is not None:
        value = float(kwargs.get("duration_seconds"))
    else:
        raise RuntimeError("Cost calculation uncertainty for Runway Act-Two: duration_seconds is required.")
    return value


def _content_moderation(model, kwargs):
    if kwargs.get("content_moderation") is not None:
        return kwargs.get("content_moderation")
    threshold = kwargs.get("public_figure_threshold")
    if threshold is None:
        return None
    validate_enum("public_figure_threshold", threshold, ["auto", "low"], PROVIDER, model)
    return {"publicFigureThreshold": threshold}


def _character(prepared):
    if prepared["image"] and prepared["video"]:
        raise ValueError("Runway Act-Two requires either a character image or character video, not both.")
    if prepared["image"]:
        return {"type": "image", "uri": prepared["image"]}
    if prepared["video"]:
        return {"type": "video", "uri": prepared["video"]}
    raise ValueError("Runway Act-Two requires image_path/image_url or video_path/video_url as the character.")


def _build_payload(model, prepared, kwargs):
    validate_allowed_kwargs(kwargs, DOCUMENTED_MODEL_OPTIONS.get(model, set()), model, PROVIDER, "motion_control", COMMON_OPTIONS)
    if not prepared["reference"]:
        raise ValueError("Runway Act-Two requires reference_path or reference_url as the driving performance video.")
    validate_enum("ratio", kwargs.get("ratio"), RATIOS, PROVIDER, model)
    validate_number("seed", kwargs.get("seed"), 0, 4294967295, PROVIDER, model)
    validate_number("expression_intensity", kwargs.get("expression_intensity"), 1, 5, PROVIDER, model)
    validate_number("expressionIntensity", kwargs.get("expressionIntensity"), 1, 5, PROVIDER, model)
    payload = {
        "model": model,
        "character": _character(prepared),
        "reference": {"type": "video", "uri": prepared["reference"]},
    }
    if prepared.get("prompt"):
        payload["promptText"] = prepared["prompt"]
    if kwargs.get("body_control") is not None:
        payload["bodyControl"] = bool(kwargs.get("body_control"))
    if kwargs.get("bodyControl") is not None:
        payload["bodyControl"] = bool(kwargs.get("bodyControl"))
    if kwargs.get("expression_intensity") is not None:
        payload["expressionIntensity"] = int(kwargs.get("expression_intensity"))
    if kwargs.get("expressionIntensity") is not None:
        payload["expressionIntensity"] = int(kwargs.get("expressionIntensity"))
    for name in ("ratio", "seed"):
        if name in kwargs and kwargs[name] is not None:
            payload[name] = kwargs[name]
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
    if model != DEFAULT_MODEL:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_credits": 0.0,
            "credit_source": "unavailable",
            "cost_reason": f"No documented pricing metadata is available for Runway model `{model}`.",
        }
    duration = _duration(kwargs)
    credits = 5 * duration
    return {
        "cost_usd": credits * CREDIT_TO_USD,
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_credits": credits,
        "credit_source": "Runway API credit pricing and published credit purchase rate",
        "cost_reason": "Runway task responses do not expose per-task credits; wrapper estimates Act-Two cost from official credits per second and caller-supplied duration_seconds.",
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


def generate_motion_control(prompt=None, image_path=None, image_url=None, video_path=None, video_url=None, reference_path=None, reference_url=None, output_path=None, sync=True, **kwargs):
    model = _selected_model(kwargs)
    prepared = prepare_motion_control(prompt, image_path, image_url, video_path, video_url, reference_path, reference_url, output_path)
    payload = _build_payload(model, prepared, kwargs)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    submission = runway_submit("/v1/character_performance", payload, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    task_id = _task_id(submission)
    async_refs = runway_async_refs(submission, task_id)

    if not sync:
        extra = {**async_refs, "cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
        return build_result(PROVIDER, model, "submitted", task_id, None, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], submission, extra)

    raw = runway_wait_for_task(
        task_id,
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
        poll_interval_seconds=kwargs.get("poll_interval_seconds"),
        task_url=async_refs.get("task_url"),
        status_url=async_refs.get("status_url"),
        result_url=async_refs.get("result_url"),
        poll_url=async_refs.get("poll_url"),
    )
    video_url = _video_url(raw)
    if not video_url:
        raise RuntimeError(f"Runway Act-Two task {task_id} did not include an output video URL.")
    extra = {**async_refs, "cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model, "completed", task_id, video_url, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], {"submission": submission, "result": raw}, extra)


def get_generation_status(request_id, **kwargs):
    model = _selected_model(kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    refs = merge_async_refs(None, kwargs, **runway_async_refs({}, request_id))
    raw = runway_get_task(
        request_id,
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
        task_url=refs.get("task_url"),
        status_url=refs.get("status_url"),
        result_url=refs.get("result_url"),
        poll_url=refs.get("poll_url"),
    )
    return {"provider": PROVIDER, "model": model, "request_id": request_id, "status": normalize_runway_status(raw.get("status")), "raw_response": raw, **refs}


def get_generation_result(request_id, output_path=None, **kwargs):
    model = _selected_model(kwargs)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "Runway")
    refs = merge_async_refs(None, kwargs, **runway_async_refs({}, request_id))
    raw = runway_get_task(
        request_id,
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
        task_url=refs.get("task_url"),
        status_url=refs.get("status_url"),
        result_url=refs.get("result_url"),
        poll_url=refs.get("poll_url"),
    )
    status = normalize_runway_status(raw.get("status"))
    if status != "completed":
        raise RuntimeError(f"Runway task {request_id} is not complete. Current status: {status}.")
    video_url = _video_url(raw)
    if not video_url:
        raise RuntimeError(f"Runway Act-Two task {request_id} did not include an output video URL.")
    extra = {**refs, "cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
