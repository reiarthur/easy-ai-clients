"""fal.ai motion-control wrapper."""

from ..._shared import (
    extract_video_url,
    fal_get_result,
    fal_get_status,
    fal_response_url,
    fal_status_url,
    fal_submit,
    fal_wait_for_result,
    normalize_fal_status,
    require_env,
    validate_allowed_kwargs,
    validate_enum,
)
from ..post_processing import build_result
from ..pre_processing import prepare_motion_control

PROVIDER = "falai"
ENV_NAME = "FAL_KEY"
DEFAULT_MODEL = "fal-ai/kling-video/v2.6/standard/motion-control"
COST_SOURCE = "fal_model_pricing_seconds_snapshot_2026-05-13"

MODEL_OPTIONS = {
    DEFAULT_MODEL: {
        "character_orientation",
        "keep_original_sound",
        "duration_seconds",
        "billing_duration_seconds",
    },
}

COMMON_OPTIONS = {"model", "timeout_seconds", "poll_interval_seconds", "extra_payload"}


def _selected_model(kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    if model not in MODEL_OPTIONS:
        raise ValueError(f"Unsupported fal.ai motion-control model: {model}.")
    return model


def _build_payload(model, prepared, kwargs):
    validate_allowed_kwargs(kwargs, MODEL_OPTIONS[model], model, PROVIDER, "motion_control", COMMON_OPTIONS)
    orientation = kwargs.get("character_orientation")
    validate_enum("character_orientation", orientation, ["image", "video"], PROVIDER, model)
    if not orientation:
        raise ValueError("fal.ai Kling motion-control requires character_orientation set to image or video.")
    if not prepared["image"]:
        raise ValueError("fal.ai Kling motion-control requires image_path or image_url for the character image.")
    if not prepared["video"]:
        raise ValueError("fal.ai Kling motion-control requires video_path or video_url for the motion reference.")
    payload = {
        "image_url": prepared["image"],
        "video_url": prepared["video"],
        "character_orientation": orientation,
        "keep_original_sound": bool(kwargs.get("keep_original_sound", True)),
    }
    if prepared["prompt"]:
        payload["prompt"] = prepared["prompt"]
    if "extra_payload" in kwargs:
        from ..._shared import merge_extra_payload

        payload = merge_extra_payload(payload, kwargs)
    return payload


def _cost(model, kwargs):
    if kwargs.get("billing_duration_seconds") is not None:
        duration_seconds = float(kwargs.get("billing_duration_seconds"))
    elif kwargs.get("duration_seconds") is not None:
        duration_seconds = float(kwargs.get("duration_seconds"))
    else:
        raise RuntimeError("Cost calculation uncertainty for fal.ai motion-control: duration_seconds is required.")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be greater than zero for fal.ai motion-control cost calculation.")
    return {
        "cost_usd": duration_seconds * 0.07,
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_reason": "fal.ai Kling motion-control pricing is documented per generated second; caller supplies duration_seconds for preflight cost estimation.",
    }


def _request_id(submission):
    request_id = submission.get("request_id") or submission.get("requestId")
    if not request_id:
        raise RuntimeError("fal.ai submission did not return a request_id.")
    return request_id


def generate_motion_control(prompt=None, image_path=None, image_url=None, video_path=None, video_url=None, reference_path=None, reference_url=None, output_path=None, sync=True, **kwargs):
    if reference_path or reference_url:
        raise ValueError("fal.ai Kling motion-control uses video_path or video_url as the motion reference; reference_path and reference_url are not supported.")
    model = _selected_model(kwargs)
    prepared = prepare_motion_control(prompt, image_path, image_url, video_path, video_url, reference_path, reference_url, output_path)
    payload = _build_payload(model, prepared, kwargs)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "fal.ai")
    submission = fal_submit(model, payload, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    request_id = _request_id(submission)

    if not sync:
        extra = {
            "status_url": submission.get("status_url") or fal_status_url(model, request_id),
            "response_url": submission.get("response_url") or fal_response_url(model, request_id),
            "cost_reason": cost["cost_reason"],
        }
        return build_result(PROVIDER, model, "submitted", request_id, None, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], submission, extra)

    raw = fal_wait_for_result(model, request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"), poll_interval_seconds=kwargs.get("poll_interval_seconds"))
    response = raw.get("response") or {}
    video_url_value = extract_video_url(response)
    if not video_url_value:
        raise RuntimeError(f"fal.ai motion-control result for {request_id} did not include a video URL.")
    extra = {"cost_reason": cost["cost_reason"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url_value, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def get_generation_status(request_id, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    if model not in MODEL_OPTIONS:
        raise ValueError(f"Unsupported fal.ai motion-control model: {model}.")
    api_key = require_env(ENV_NAME, "fal.ai")
    raw = fal_get_status(model, request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    return {"provider": PROVIDER, "model": model, "request_id": request_id, "status": normalize_fal_status(raw.get("status")), "raw_response": raw}


def get_generation_result(request_id, output_path=None, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    if model not in MODEL_OPTIONS:
        raise ValueError(f"Unsupported fal.ai motion-control model: {model}.")
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "fal.ai")
    raw = fal_get_result(model, request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    video_url_value = extract_video_url(raw)
    if not video_url_value:
        raise RuntimeError(f"fal.ai motion-control result for {request_id} did not include a video URL.")
    from ..._shared import normalize_output_path

    extra = {"cost_reason": cost["cost_reason"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url_value, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        from ..._shared import download_file, normalize_output_path

        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
