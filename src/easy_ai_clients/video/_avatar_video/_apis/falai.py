"""fal.ai avatar-video wrapper."""

from ..._falai_pricing import FAL_ESTIMATE_OPTIONS, fal_pricing_estimate
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
)
from ..post_processing import build_result
from ..pre_processing import prepare_avatar_video

PROVIDER = "falai"
ENV_NAME = "FAL_KEY"
DEFAULT_MODEL = "fal-ai/longcat-single-avatar/image-audio-to-video"
COST_SOURCE = "fal_model_pricing_snapshot_2026-05-14"

DOCUMENTED_MODEL_PRICING = {
    "veed/fabric-1.0": {"price_usd": 0.00017, "unit": "compute_seconds"},
    "veed/fabric-1.0/fast": {"price_usd": 0.00017, "unit": "compute_seconds"},
    "fal-ai/flashtalk": {"price_usd": 0.02, "unit": "seconds"},
    DEFAULT_MODEL: {"price_usd": 0.15, "unit": "longcat_units"},
    "fal-ai/longcat-multi-avatar/image-audio-to-video": {"price_usd": 0.15, "unit": "longcat_units"},
    "fal-ai/ai-avatar": {"price_usd": 0.2, "unit": "seconds"},
    "fal-ai/infinitalk": {"price_usd": 0.2, "unit": "seconds"},
    "fal-ai/echomimic-v3": {"price_usd": 0.2, "unit": "seconds"},
    "fal-ai/wan/v2.2-14b/speech-to-video": {"price_usd": 0.2, "unit": "seconds"},
    "fal-ai/creatify/aurora": {"price_usd": 1.0, "unit": "units"},
}

COMMON_OPTIONS = {"model", "timeout_seconds", "poll_interval_seconds", "extra_payload", *FAL_ESTIMATE_OPTIONS}


def _selected_model(kwargs):
    return kwargs.get("model", DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    payload = {}
    if prepared["image"]:
        payload["image_url"] = prepared["image"]
    if prepared["audio"]:
        payload["audio_url"] = prepared["audio"]
    if prepared["text"]:
        payload["text"] = prepared["text"]
    for name, value in kwargs.items():
        if name not in COMMON_OPTIONS and name not in payload and value is not None:
            payload[name] = value
    if "extra_payload" in kwargs:
        from ..._shared import merge_extra_payload

        payload = merge_extra_payload(payload, kwargs)
    return payload


def _quantity_for_unit(unit, kwargs):
    if unit == "seconds":
        value = kwargs.get("billing_duration_seconds", kwargs.get("duration_seconds", kwargs.get("duration")))
        return float(value) if value is not None else None
    if unit == "compute_seconds":
        value = kwargs.get("billing_compute_seconds", kwargs.get("compute_seconds"))
        return float(value) if value is not None else None
    if unit == "units":
        value = kwargs.get("billing_units", kwargs.get("units"))
        return float(value) if value is not None else None
    if unit == "longcat_units":
        if kwargs.get("billing_units") is not None:
            return float(kwargs.get("billing_units"))
        resolution = kwargs.get("resolution", "480p")
        segments = int(kwargs.get("num_segments", 1))
        billed_seconds = 5.8 + max(0, segments - 1) * 5
        units_per_second = 4 if resolution == "720p" else 1
        return billed_seconds * units_per_second
    return None


def _cost(model, kwargs):
    estimate = fal_pricing_estimate(model, kwargs, ENV_NAME)
    if estimate is not None:
        return estimate
    if model not in DOCUMENTED_MODEL_PRICING:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_reason": f"No documented pricing metadata is available for fal.ai model `{model}`.",
        }
    pricing = DOCUMENTED_MODEL_PRICING[model]
    quantity = _quantity_for_unit(pricing["unit"], kwargs)
    if quantity is None:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_reason": (
                f"fal.ai pricing for `{model}` is documented per {pricing['unit']}, "
                "but this wrapper cannot infer the billable quantity without an explicit billing kwarg."
            ),
        }
    return {
        "cost_usd": pricing["price_usd"] * quantity,
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_reason": f"fal.ai pricing is estimated from documented {pricing['unit']} pricing; usage reconciliation is not performed during safe wrapper execution.",
    }


def _request_id(submission):
    request_id = submission.get("request_id") or submission.get("requestId")
    if not request_id:
        raise RuntimeError("fal.ai submission did not return a request_id.")
    return request_id


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
        return build_result(
            PROVIDER,
            model,
            "submitted",
            request_id,
            None,
            prepared["output_path"],
            cost["cost_usd"],
            cost["cost_is_estimated"],
            cost["cost_source"],
            submission,
            extra,
        )

    raw = fal_wait_for_result(
        model,
        request_id,
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
        poll_interval_seconds=kwargs.get("poll_interval_seconds"),
    )
    response = raw.get("response") or {}
    video_url = extract_video_url(response)
    if not video_url:
        raise RuntimeError(f"fal.ai avatar-video result for {request_id} did not include a video URL.")
    extra = {"cost_reason": cost["cost_reason"]}
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
        raw,
        extra,
    )


def get_generation_status(request_id, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    api_key = require_env(ENV_NAME, "fal.ai")
    raw = fal_get_status(model, request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    return {
        "provider": PROVIDER,
        "model": model,
        "request_id": request_id,
        "status": normalize_fal_status(raw.get("status")),
        "raw_response": raw,
    }


def get_generation_result(request_id, output_path=None, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    cost = _cost(model, kwargs)
    api_key = require_env(ENV_NAME, "fal.ai")
    raw = fal_get_result(model, request_id, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    video_url = extract_video_url(raw)
    if not video_url:
        raise RuntimeError(f"fal.ai avatar-video result for {request_id} did not include a video URL.")
    from ..._shared import normalize_output_path

    extra = {"cost_reason": cost["cost_reason"]}
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
        extra,
    )


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        from ..._shared import download_file, normalize_output_path

        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
