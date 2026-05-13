"""fal.ai text-to-video wrapper."""

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
    validate_number,
)
from ..post_processing import build_result
from ..pre_processing import prepare_text_to_video

PROVIDER = "falai"
ENV_NAME = "FAL_KEY"
DEFAULT_MODEL = "fal-ai/wan/v2.2-5b/text-to-video/distill"
COST_SOURCE = "fal_model_pricing_units_snapshot_2026-05-13"

MODEL_PRICES = {
    DEFAULT_MODEL: {"price_usd": 0.08, "unit": "video"},
}

MODEL_OPTIONS = {
    DEFAULT_MODEL: {
        "num_frames",
        "frames_per_second",
        "seed",
        "resolution",
        "aspect_ratio",
        "num_inference_steps",
        "enable_safety_checker",
        "enable_output_safety_checker",
        "enable_prompt_expansion",
        "guidance_scale",
        "shift",
        "interpolator_model",
        "num_interpolated_frames",
        "adjust_fps_for_interpolation",
        "video_quality",
        "video_write_mode",
    },
}

COMMON_OPTIONS = {"model", "timeout_seconds", "poll_interval_seconds", "extra_payload"}


def _selected_model(kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    if model not in MODEL_OPTIONS:
        raise ValueError(f"Unsupported fal.ai text-to-video model: {model}.")
    return model


def _build_payload(model, prepared, kwargs):
    validate_allowed_kwargs(kwargs, MODEL_OPTIONS[model], model, PROVIDER, "text_to_video", COMMON_OPTIONS)
    validate_enum("resolution", kwargs.get("resolution"), ["580p", "720p"], PROVIDER, model)
    validate_enum("aspect_ratio", kwargs.get("aspect_ratio"), ["16:9", "9:16", "1:1"], PROVIDER, model)
    validate_enum("interpolator_model", kwargs.get("interpolator_model"), ["none", "film", "rife"], PROVIDER, model)
    validate_enum("video_quality", kwargs.get("video_quality"), ["low", "medium", "high", "maximum"], PROVIDER, model)
    validate_enum("video_write_mode", kwargs.get("video_write_mode"), ["fast", "balanced", "small"], PROVIDER, model)
    validate_number("num_frames", kwargs.get("num_frames"), 17, 161, PROVIDER, model)
    validate_number("frames_per_second", kwargs.get("frames_per_second"), 4, 60, PROVIDER, model)
    validate_number("seed", kwargs.get("seed"), 0, 4294967295, PROVIDER, model)
    validate_number("num_inference_steps", kwargs.get("num_inference_steps"), 2, 50, PROVIDER, model)
    validate_number("guidance_scale", kwargs.get("guidance_scale"), 1, 10, PROVIDER, model)
    validate_number("shift", kwargs.get("shift"), 1, 10, PROVIDER, model)
    validate_number("num_interpolated_frames", kwargs.get("num_interpolated_frames"), 0, 4, PROVIDER, model)

    payload = {"prompt": prepared["prompt"]}
    for name in MODEL_OPTIONS[model]:
        if name in kwargs and kwargs[name] is not None:
            payload[name] = kwargs[name]
    if "extra_payload" in kwargs:
        from ..._shared import merge_extra_payload

        payload = merge_extra_payload(payload, kwargs)
    return payload


def _cost(model, kwargs):
    price = MODEL_PRICES[model]["price_usd"]
    return {
        "cost_usd": price,
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_reason": "fal.ai pricing is documented per generated video; usage reconciliation is not performed during safe wrapper execution.",
    }


def _request_id(submission):
    request_id = submission.get("request_id") or submission.get("requestId")
    if not request_id:
        raise RuntimeError("fal.ai submission did not return a request_id.")
    return request_id


def generate_text_to_video(prompt, output_path=None, sync=True, **kwargs):
    model = _selected_model(kwargs)
    prepared = prepare_text_to_video(prompt, output_path)
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
    video_url = extract_video_url(response)
    if not video_url:
        raise RuntimeError(f"fal.ai text-to-video result for {request_id} did not include a video URL.")
    extra = {"cost_reason": cost["cost_reason"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def get_generation_status(request_id, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    if model not in MODEL_OPTIONS:
        raise ValueError(f"Unsupported fal.ai text-to-video model: {model}.")
    api_key = require_env(ENV_NAME, "fal.ai")
    raw = fal_get_status(model, request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    return {"provider": PROVIDER, "model": model, "request_id": request_id, "status": normalize_fal_status(raw.get("status")), "raw_response": raw}


def get_generation_result(request_id, output_path=None, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    if model not in MODEL_OPTIONS:
        raise ValueError(f"Unsupported fal.ai text-to-video model: {model}.")
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "fal.ai")
    raw = fal_get_result(model, request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    video_url = extract_video_url(raw)
    if not video_url:
        raise RuntimeError(f"fal.ai text-to-video result for {request_id} did not include a video URL.")
    prepared_output = prepare_text_to_video("placeholder", output_path)["output_path"]
    extra = {"cost_reason": cost["cost_reason"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url, prepared_output, cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        from ..._shared import download_file, normalize_output_path

        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
