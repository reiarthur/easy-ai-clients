"""Hedra video-to-video wrapper."""

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

DEFAULT_MODEL = "kling-o3-standard-edit-v2v"
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
    return resolve_model(kwargs.get("model"), DEFAULT_MODEL, "video_to_video")


def _local_or_id_asset_id(path, url, asset_id, asset_type, api_key, timeout_seconds=None):
    if path and asset_id:
        raise ValueError(f"Provide either {asset_type}_path or {asset_type}_id, not both.")
    if url:
        raise ValueError(
            f"Hedra video_to_video requires a Hedra {asset_type} asset id or local file; "
            f"remote {asset_type}_url is not accepted for this endpoint."
        )
    if asset_id:
        return str(asset_id).strip()
    if path:
        return hedra_upload_local_asset(path, asset_type, api_key, timeout_seconds)
    return None


def _reference_image_ids(image_path, image_url, reference_path, reference_url, kwargs, api_key):
    ids = list(kwargs.get("reference_image_asset_ids") or kwargs.get("reference_image_ids") or [])
    single_id = kwargs.get("reference_image_asset_id") or kwargs.get("reference_image_id")
    if single_id:
        ids.append(single_id)
    for path, url, name in (
        (image_path, image_url, "image"),
        (reference_path, reference_url, "reference"),
    ):
        asset_id = _local_or_id_asset_id(
            path,
            url,
            kwargs.get(f"{name}_asset_id") or kwargs.get(f"{name}_id"),
            "image",
            api_key,
            kwargs.get("timeout_seconds"),
        )
        if asset_id:
            ids.append(asset_id)
    return [str(value).strip() for value in ids if str(value).strip()]


def _build_payload(model_data, prompt, video_path, video_url, image_path, image_url, reference_path, reference_url, kwargs):
    api_key = require_env(ENV_NAME, "Hedra")
    prompt_text = str(prompt or kwargs.get("prompt") or "").strip()
    if not prompt_text:
        raise ValueError("Hedra video_to_video requires prompt.")
    video_id = _local_or_id_asset_id(
        video_path,
        video_url,
        kwargs.get("video_id") or kwargs.get("video_asset_id"),
        "video",
        api_key,
        kwargs.get("timeout_seconds"),
    )
    if not video_id:
        raise ValueError("Hedra video_to_video requires video_id, video_asset_id, or a local video_path.")
    payload = {
        "type": "video_to_video",
        "ai_model_id": model_data["id"],
        "video_id": video_id,
        "prompt": prompt_text,
        "generated_video_inputs": generated_video_inputs(prompt_text, model_data, kwargs),
    }
    if kwargs.get("keep_audio") is not None:
        payload["keep_audio"] = bool(kwargs["keep_audio"])
    reference_image_ids = _reference_image_ids(
        image_path,
        image_url,
        reference_path,
        reference_url,
        kwargs,
        api_key,
    )
    if reference_image_ids:
        payload["reference_image_ids"] = reference_image_ids
    if kwargs.get("elements") is not None:
        payload["elements"] = kwargs["elements"]
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
                "image_id",
                "image_asset_id",
                "reference_id",
                "reference_asset_id",
                "reference_image_id",
                "reference_image_asset_id",
                "reference_image_ids",
                "reference_image_asset_ids",
                "keep_audio",
                "elements",
            }
            and name not in payload
            and value is not None
        ):
            payload[name] = value
    if "extra_payload" in kwargs:
        payload = merge_extra_payload(payload, kwargs)
    return payload


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
    _, model_data = _selected_model(kwargs)
    payload = _build_payload(
        model_data,
        prompt,
        video_path,
        video_url,
        image_path,
        image_url,
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
