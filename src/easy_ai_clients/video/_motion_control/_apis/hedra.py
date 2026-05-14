"""Hedra motion-control wrapper."""

from ..._hedra_common import (
    ENV_NAME,
    PROVIDER,
    generated_video_inputs,
    hedra_cost,
    hedra_extract_video_url,
    hedra_get_generation_status,
    hedra_status_result,
    resolve_model,
    submit_generation,
)
from ..._shared import (
    download_file,
    hedra_upload_local_asset,
    merge_extra_payload,
    normalize_output_path,
    require_env,
)
from ..post_processing import build_result

DEFAULT_MODEL = "kling-2.6-motion-control-standard-vi2v"
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
}


def _selected_model(kwargs):
    return resolve_model(kwargs.get("model"), DEFAULT_MODEL, "motion_control")


def _local_or_id_asset_id(path, url, asset_id, asset_type, api_key, timeout_seconds=None):
    if path and asset_id:
        raise ValueError(f"Provide either {asset_type}_path or {asset_type}_id, not both.")
    if url:
        raise ValueError(
            f"Hedra motion_control requires a Hedra {asset_type} asset id or local file; "
            f"remote {asset_type}_url is not accepted for this endpoint."
        )
    if asset_id:
        return str(asset_id).strip()
    if path:
        return hedra_upload_local_asset(path, asset_type, api_key, timeout_seconds)
    return None


def _build_payload(model_data, prompt, image_path, image_url, video_path, video_url, reference_path, reference_url, kwargs):
    api_key = require_env(ENV_NAME, "Hedra")
    if video_path and reference_path:
        raise ValueError("Provide either video_path or reference_path for Hedra motion_control, not both.")
    if video_url and reference_url:
        raise ValueError("Provide either video_url or reference_url for Hedra motion_control, not both.")
    orientation = kwargs.get("character_orientation")
    if model_data.get("requires_character_orientation") and not orientation:
        raise ValueError("Hedra motion_control requires character_orientation.")
    video_id = _local_or_id_asset_id(
        video_path or reference_path,
        video_url or reference_url,
        kwargs.get("video_id") or kwargs.get("video_asset_id") or kwargs.get("reference_id") or kwargs.get("reference_asset_id"),
        "video",
        api_key,
        kwargs.get("timeout_seconds"),
    )
    if not video_id:
        raise ValueError("Hedra motion_control requires video_id, video_asset_id, reference_asset_id, or a local video_path/reference_path.")
    start_keyframe_id = _local_or_id_asset_id(
        image_path,
        image_url,
        kwargs.get("start_keyframe_id") or kwargs.get("image_id") or kwargs.get("image_asset_id"),
        "image",
        api_key,
        kwargs.get("timeout_seconds"),
    )
    if model_data.get("requires_start_frame") and not start_keyframe_id:
        raise ValueError("Hedra motion_control requires start_keyframe_id, image_id, image_asset_id, or a local image_path.")
    prompt_text = str(prompt or kwargs.get("prompt") or "Animate the character using the motion reference.").strip()
    payload = {
        "type": "motion_control",
        "ai_model_id": model_data["id"],
        "video_id": video_id,
        "generated_video_inputs": generated_video_inputs(prompt_text, model_data, kwargs),
    }
    if start_keyframe_id:
        payload["start_keyframe_id"] = start_keyframe_id
    if kwargs.get("batch_size") is not None:
        payload["batch_size"] = int(kwargs["batch_size"])
    for name, value in kwargs.items():
        if (
            name not in COMMON_OPTIONS
            and name not in GENERATED_INPUT_OPTIONS
            and name
            not in {
                "prompt",
                "video_id",
                "video_asset_id",
                "reference_id",
                "reference_asset_id",
                "start_keyframe_id",
                "image_id",
                "image_asset_id",
            }
            and name not in payload
            and value is not None
        ):
            payload[name] = value
    if "extra_payload" in kwargs:
        payload = merge_extra_payload(payload, kwargs)
    return payload


def generate_motion_control(
    prompt=None,
    image_path=None,
    image_url=None,
    video_path=None,
    video_url=None,
    reference_path=None,
    reference_url=None,
    output_path=None,
    sync=True,
    **kwargs,
):
    _, model_data = _selected_model(kwargs)
    payload = _build_payload(
        model_data,
        prompt,
        image_path,
        image_url,
        video_path,
        video_url,
        reference_path,
        reference_url,
        kwargs,
    )
    cost = hedra_cost(model_data, kwargs)
    normalized_output_path = normalize_output_path(output_path)
    model_name, request_id, status, video_url_value, normalized_output_path, raw, extra = submit_generation(
        payload,
        sync,
        normalized_output_path,
        model_data,
        cost,
        kwargs,
    )
    return build_result(
        PROVIDER,
        model_name,
        status,
        request_id,
        video_url_value,
        normalized_output_path,
        cost["cost_usd"],
        cost["cost_is_estimated"],
        cost["cost_source"],
        raw,
        extra,
    )


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
