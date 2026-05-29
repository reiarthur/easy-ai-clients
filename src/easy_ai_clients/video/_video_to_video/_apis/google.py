"""Google Veo video-to-video wrapper for Gemini video extension."""

from ..._shared import (
    GOOGLE_GEMINI_BASE_URL,
    download_file,
    google_async_refs,
    google_extract_video_url,
    google_get_operation,
    google_headers,
    google_wait_for_operation,
    http_json,
    merge_async_refs,
    normalize_output_path,
    require_env,
    validate_enum,
    validate_number,
)
from ..post_processing import build_result
from ..pre_processing import prepare_video_to_video

PROVIDER = "google"
ENV_NAME = "GOOGLE_API_KEY"
DEFAULT_MODEL = "veo-3.1-generate-preview"
COST_SOURCE = "google_gemini_veo_pricing_seconds_snapshot_2026-05-14"

MODEL_ALIASES = {
    "veo-3.1-fast-generate-001": "veo-3.1-fast-generate-preview",
    "veo-3.1-generate-001": "veo-3.1-generate-preview",
}

DOCUMENTED_MODEL_DATA = {
    "veo-3.1-fast-generate-preview": {
        "durations": [8],
        "rates": {"720p": 0.10},
        "default_resolution": "720p",
        "max_videos": 1,
    },
    "veo-3.1-generate-preview": {
        "durations": [8],
        "rates": {"720p": 0.40},
        "default_resolution": "720p",
        "max_videos": 1,
    },
}

COMMON_OPTIONS = {"model", "timeout_seconds", "poll_interval_seconds", "extra_payload"}


def _selected_model(kwargs):
    return MODEL_ALIASES.get(kwargs.get("model", DEFAULT_MODEL), kwargs.get("model", DEFAULT_MODEL))


def _duration(model, kwargs):
    if model not in DOCUMENTED_MODEL_DATA:
        raise ValueError(
            f"Google Veo video_to_video extension is implemented only for Veo 3.1/3.1 Fast models; got `{model}`."
        )
    value = int(kwargs.get("duration_seconds", 8))
    if value != 8:
        raise ValueError("Google Veo video_to_video extension requires duration_seconds=8.")
    return value


def _resolution(model, kwargs):
    if model not in DOCUMENTED_MODEL_DATA:
        raise ValueError(
            f"Google Veo video_to_video extension is implemented only for Veo 3.1/3.1 Fast models; got `{model}`."
        )
    value = str(kwargs.get("resolution", DOCUMENTED_MODEL_DATA[model]["default_resolution"])).lower()
    if value != "720p":
        raise ValueError("Google Veo video_to_video extension requires resolution='720p'.")
    return value


def _number_of_videos(model, kwargs):
    if model not in DOCUMENTED_MODEL_DATA:
        raise ValueError(
            f"Google Veo video_to_video extension is implemented only for Veo 3.1/3.1 Fast models; got `{model}`."
        )
    value = int(kwargs.get("number_of_videos", 1))
    if value != 1:
        raise ValueError("Google Veo video_to_video extension requires number_of_videos=1.")
    return value


def _video_object(value):
    text = str(value or "").strip()
    if text.startswith("data:"):
        header, separator, payload = text.partition(",")
        if not separator:
            raise ValueError("video data URL is missing a base64 payload.")
        mime_type = header[5:].split(";")[0] or "video/mp4"
        return {"inlineData": {"mimeType": mime_type, "data": payload}}
    return {"uri": text}


def _build_payload(model, prepared, kwargs):
    duration = _duration(model, kwargs)
    resolution = _resolution(model, kwargs)
    number_of_videos = _number_of_videos(model, kwargs)
    aspect_ratio = kwargs.get("aspect_ratio", "16:9")
    validate_enum("aspect_ratio", aspect_ratio, ["16:9", "9:16"], PROVIDER, model)
    validate_enum("person_generation", kwargs.get("person_generation"), ["allow_all"], PROVIDER, model)
    validate_number("seed", kwargs.get("seed"), 0, 4294967295, PROVIDER, model)

    instance = {"video": _video_object(prepared["video"])}
    if prepared["prompt"]:
        instance["prompt"] = prepared["prompt"]
    parameters = {
        "durationSeconds": duration,
        "aspectRatio": aspect_ratio,
        "resolution": resolution,
    }
    if "number_of_videos" in kwargs:
        parameters["numberOfVideos"] = number_of_videos
    for source_name, target_name in {"person_generation": "personGeneration", "seed": "seed"}.items():
        if source_name in kwargs and kwargs[source_name] is not None:
            parameters[target_name] = kwargs[source_name]
    known = {"duration_seconds", "aspect_ratio", "resolution", "number_of_videos", "person_generation", "seed"}
    for name, value in kwargs.items():
        if name not in COMMON_OPTIONS and name not in known and value is not None:
            parameters[name] = value
    payload = {"instances": [instance], "parameters": parameters}
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
            "cost_reason": f"No documented pricing metadata is available for Google Veo model `{model}`.",
        }
    duration = _duration(model, kwargs)
    resolution = _resolution(model, kwargs)
    rate = DOCUMENTED_MODEL_DATA[model]["rates"][resolution]
    return {
        "cost_usd": rate * duration * _number_of_videos(model, kwargs),
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_reason": "Gemini Veo extension responses do not return per-request cost; wrapper estimates from official per-second pricing.",
    }


def _operation_name(raw):
    name = raw.get("name") or raw.get("operationName")
    if not name:
        raise RuntimeError("Google Veo submission did not return an operation name.")
    return name


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
    if image_path or image_url or reference_path or reference_url:
        raise ValueError("Google Veo video_to_video supports only a source video plus prompt; use image_to_video for frame inputs.")
    model = _selected_model(kwargs)
    prepared = prepare_video_to_video(prompt, video_path, video_url, None, None, None, None, output_path)
    payload = _build_payload(model, prepared, kwargs)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "Google Veo")
    url = GOOGLE_GEMINI_BASE_URL + "/models/" + model + ":predictLongRunning"
    submission = http_json("POST", url, headers=google_headers(api_key), payload=payload, timeout_seconds=kwargs.get("timeout_seconds"))
    operation_name = _operation_name(submission)
    async_refs = google_async_refs(submission, operation_name)

    if not sync:
        extra = {**async_refs, "cost_reason": cost["cost_reason"]}
        return build_result(PROVIDER, model, "submitted", operation_name, None, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], submission, extra)

    operation = google_wait_for_operation(
        operation_name,
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
        poll_interval_seconds=kwargs.get("poll_interval_seconds"),
        operation_url=async_refs.get("operation_url"),
    )
    video_url_value = google_extract_video_url(operation)
    if not video_url_value:
        raise RuntimeError(f"Google Veo operation {operation_name} did not include a downloadable video URI.")
    extra = {**async_refs, "cost_reason": cost["cost_reason"]}
    raw_response = {"submission": submission, "result": operation}
    return build_result(PROVIDER, model, "completed", operation_name, video_url_value, prepared["output_path"], cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw_response, extra, download_headers=google_headers(api_key))


def get_generation_status(request_id, **kwargs):
    model = _selected_model(kwargs)
    api_key = require_env(ENV_NAME, "Google Veo")
    refs = merge_async_refs(None, kwargs, **google_async_refs({}, request_id))
    raw = google_get_operation(
        request_id,
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
        operation_url=refs.get("operation_url"),
    )
    status = "completed" if raw.get("done") is True else "running"
    if raw.get("error"):
        status = "failed"
    return {"provider": PROVIDER, "model": model, "request_id": request_id, "operation_name": request_id, "status": status, "raw_response": raw, **refs}


def get_generation_result(request_id, output_path=None, **kwargs):
    model = _selected_model(kwargs)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "Google Veo")
    refs = merge_async_refs(None, kwargs, **google_async_refs({}, request_id))
    raw = google_get_operation(
        request_id,
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
        operation_url=refs.get("operation_url"),
    )
    if raw.get("done") is not True:
        raise RuntimeError(f"Google Veo operation {request_id} is not complete.")
    if raw.get("error"):
        raise RuntimeError(f"Google Veo operation failed: {raw.get('error')}")
    video_url_value = google_extract_video_url(raw)
    if not video_url_value:
        raise RuntimeError(f"Google Veo operation {request_id} did not include a downloadable video URI.")
    extra = {**refs, "operation_name": request_id, "cost_reason": cost["cost_reason"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url_value, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra, download_headers=google_headers(api_key))


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        api_key = require_env(ENV_NAME, "Google Veo")
        return download_file(video_url, normalize_output_path(output_path), headers=google_headers(api_key))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
