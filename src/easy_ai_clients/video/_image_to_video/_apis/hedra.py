"""Hedra image-to-video wrapper."""

from ..._hedra_common import (
    ENV_NAME,
    PROVIDER,
    generated_video_inputs,
    hedra_cost,
    hedra_extract_video_url,
    hedra_get_generation_status,
    hedra_status_result,
    media_payload_key,
    resolve_model,
    submit_generation,
)
from ..._shared import (
    clean_text,
    download_file,
    merge_extra_payload,
    normalize_output_path,
    require_env,
)
from ..post_processing import build_result

DEFAULT_MODEL = "minimax-hailuo-2.3-fast-standard-i2v"
COMMON_OPTIONS = {"model", "timeout_seconds", "poll_interval_seconds", "extra_payload"}
GENERATED_INPUT_OPTIONS = {
    "duration_ms",
    "duration_seconds",
    "duration",
    "billing_duration_seconds",
    "aspect_ratio",
    "resolution",
    "batch_size",
    "number_of_videos",
    "enhance_prompt",
    "bounding_box_target",
    "character_orientation",
    "start_keyframe_id",
    "start_keyframe_url",
}


def _selected_model(kwargs):
    return resolve_model(kwargs.get("model"), DEFAULT_MODEL, "image_to_video")


def _build_payload(model_data, prompt, image_path, image_url, kwargs):
    api_key = require_env(ENV_NAME, "Hedra")
    inputs = generated_video_inputs(clean_text(prompt, "prompt"), model_data, kwargs)
    start_keyframe_id = kwargs.get("start_keyframe_id")
    start_keyframe_url = kwargs.get("start_keyframe_url")
    if not start_keyframe_id and not start_keyframe_url:
        key, value = media_payload_key(image_path, image_url, "image", api_key, kwargs.get("timeout_seconds"))
        if key == "id":
            start_keyframe_id = value
        elif key == "url":
            start_keyframe_url = value
    if not start_keyframe_id and not start_keyframe_url:
        raise ValueError("Hedra image_to_video requires image, image_path, image_url, start_keyframe_id, or start_keyframe_url.")
    payload = {
        "type": "video",
        "ai_model_id": model_data["id"],
        "generated_video_inputs": inputs,
    }
    if start_keyframe_id:
        payload["start_keyframe_id"] = start_keyframe_id
    if start_keyframe_url:
        payload["start_keyframe_url"] = start_keyframe_url
    if kwargs.get("batch_size") is not None:
        payload["batch_size"] = int(kwargs["batch_size"])
    for name, value in kwargs.items():
        if name not in COMMON_OPTIONS and name not in GENERATED_INPUT_OPTIONS and name not in payload and value is not None:
            payload[name] = value
    if "extra_payload" in kwargs:
        payload = merge_extra_payload(payload, kwargs)
    return payload


def generate_image_to_video(prompt, image_path=None, image_url=None, output_path=None, sync=True, **kwargs):
    _, model_data = _selected_model(kwargs)
    payload = _build_payload(model_data, prompt, image_path, image_url, kwargs)
    cost = hedra_cost(model_data, kwargs)
    normalized_output_path = normalize_output_path(output_path)
    model_name, request_id, status, video_url, normalized_output_path, raw, extra = submit_generation(
        payload,
        sync,
        normalized_output_path,
        model_data,
        cost,
        kwargs,
    )
    return build_result(PROVIDER, model_name, status, request_id, video_url, normalized_output_path, cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def get_generation_status(request_id, **kwargs):
    _, model_data = _selected_model(kwargs)
    return hedra_status_result(request_id, model_data, kwargs)


def get_generation_result(request_id, output_path=None, **kwargs):
    _, model_data = _selected_model(kwargs)
    cost = hedra_cost(model_data, kwargs)
    api_key = require_env(ENV_NAME, "Hedra")
    raw = hedra_get_generation_status(request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    video_url = hedra_extract_video_url(raw)
    if not video_url:
        raise RuntimeError(f"Hedra generation {request_id} did not include a downloadable video URL.")
    extra = {"cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model_data["name"], "completed", request_id, video_url, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
