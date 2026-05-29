"""Runway avatar-video wrapper."""

import math

from ..._shared import (
    download_file,
    merge_async_refs,
    normalize_output_path,
    normalize_runway_status,
    require_env,
    runway_async_refs,
    runway_get_task,
    runway_media_uri,
    runway_submit,
    runway_wait_for_task,
)
from ..post_processing import build_result

PROVIDER = "runway"
ENV_NAME = "RUNWAYML_API_SECRET"
DEFAULT_MODEL = "gwm1_avatars"
COST_SOURCE = "runway_api_realtime_pricing_credits_snapshot_2026-05-14"
CREDIT_TO_USD = 0.01
COMMON_OPTIONS = {
    "model",
    "timeout_seconds",
    "poll_interval_seconds",
    "extra_payload",
    "create_avatar",
    "name",
    "personality",
    "avatar_voice",
}


def _selected_model(kwargs):
    return kwargs.get("model", DEFAULT_MODEL)


def _avatar_object(avatar, kwargs):
    if isinstance(avatar, dict):
        normalized = dict(avatar)
        if "preset_id" in normalized and "presetId" not in normalized:
            normalized["presetId"] = normalized.pop("preset_id")
        if "avatar_id" in normalized and "avatarId" not in normalized:
            normalized["avatarId"] = normalized.pop("avatar_id")
        return normalized
    if kwargs.get("avatar_id"):
        return {"type": "custom", "avatarId": kwargs.get("avatar_id")}
    if kwargs.get("preset_id"):
        return {"type": "runway-preset", "presetId": kwargs.get("preset_id")}
    if isinstance(avatar, str) and avatar.strip():
        return {"type": "runway-preset", "presetId": avatar.strip()}
    raise ValueError("Runway avatar_video requires avatar, avatar_id, or preset_id.")


def _speech_voice(voice):
    if isinstance(voice, dict):
        normalized = dict(voice)
        if "preset_id" in normalized and "presetId" not in normalized:
            normalized["presetId"] = normalized.pop("preset_id")
        return normalized
    if isinstance(voice, str) and voice.strip():
        return {"type": "preset", "presetId": voice.strip()}
    return None


def _speech_object(text, audio_url, kwargs):
    if isinstance(kwargs.get("speech"), dict):
        speech = dict(kwargs["speech"])
        if "voice" in speech:
            speech["voice"] = _speech_voice(speech["voice"]) or speech["voice"]
        return speech
    if audio_url:
        return {"type": "audio", "audio": audio_url}
    if text:
        speech = {"type": "text", "text": text}
        if kwargs.get("voice"):
            speech["voice"] = _speech_voice(kwargs["voice"])
        return speech
    raise ValueError("Runway avatar_video requires audio or text.")


def _build_payload(model, avatar, text, audio_url, kwargs):
    payload = {
        "model": model,
        "avatar": _avatar_object(avatar, kwargs),
        "speech": _speech_object(text, audio_url, kwargs),
    }
    for name, value in kwargs.items():
        if name not in COMMON_OPTIONS and name not in {"avatar_id", "preset_id", "speech", "voice"} and name not in payload and value is not None:
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
    value = kwargs.get("billing_duration_seconds", kwargs.get("duration_seconds", kwargs.get("duration")))
    if value is None:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_credits": 0.0,
            "credit_source": "Runway API real-time pricing",
            "cost_reason": "Runway gwm1_avatars pricing needs duration_seconds to estimate the 2 upfront credits plus 2 credits per 6 seconds.",
        }
    credits = 2 + 2 * math.ceil(float(value) / 6.0)
    return {
        "cost_usd": credits * CREDIT_TO_USD,
        "cost_is_estimated": True,
        "cost_source": COST_SOURCE,
        "cost_credits": credits,
        "credit_source": "Runway API real-time pricing and published credit purchase rate",
        "cost_reason": "Runway gwm1_avatars cost is estimated as 2 upfront credits plus 2 credits per 6 seconds.",
    }


def _task_id(raw):
    task_id = raw.get("id") or raw.get("taskId")
    if not task_id:
        raise RuntimeError("Runway avatar-video submission did not return a task id.")
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
    return raw.get("video_url") or raw.get("url") if isinstance(raw, dict) else None


def generate_avatar_video(
    avatar=None,
    image_path=None,
    image_url=None,
    audio_path=None,
    audio_url=None,
    text=None,
    output_path=None,
    sync=True,
    **kwargs,
):
    api_key = require_env(ENV_NAME, "Runway")
    if image_path or image_url:
        if not kwargs.get("create_avatar"):
            raise ValueError("Runway avatar_video with image requires create_avatar=True so a custom avatar can be created first.")
        from ..._create_avatar._apis import runway as create_avatar_provider

        create_result = create_avatar_provider.create_avatar(
            image_path=image_path,
            image_url=image_url,
            name=kwargs.get("name"),
            voice=kwargs.get("avatar_voice", kwargs.get("voice")),
            personality=kwargs.get("personality"),
            timeout_seconds=kwargs.get("timeout_seconds"),
        )
        avatar = {"type": "custom", "avatarId": create_result["avatar_id"]}
    audio_uri = runway_media_uri(
        audio_path,
        audio_url,
        "audio_path",
        "audio_url",
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    model = _selected_model(kwargs)
    payload = _build_payload(model, avatar, text, audio_uri, kwargs)
    cost = _cost(model, kwargs)
    submission = runway_submit("/v1/avatar_videos", payload, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    task_id = _task_id(submission)
    normalized_output_path = normalize_output_path(output_path)
    async_refs = runway_async_refs(submission, task_id)

    if not sync:
        extra = {**async_refs, "cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
        return build_result(PROVIDER, model, "submitted", task_id, None, normalized_output_path, cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], submission, extra)

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
        raise RuntimeError(f"Runway avatar-video task {task_id} did not include an output video URL.")
    extra = {**async_refs, "cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model, "completed", task_id, video_url, normalized_output_path, cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], {"submission": submission, "result": raw}, extra)


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
        raise RuntimeError(f"Runway avatar-video task {request_id} did not include an output video URL.")
    extra = {**refs, "cost_reason": cost["cost_reason"], "cost_credits": cost["cost_credits"], "credit_source": cost["credit_source"]}
    return build_result(PROVIDER, model, "completed", request_id, video_url, normalize_output_path(output_path), cost["cost_usd"], cost["cost_is_estimated"], cost["cost_source"], raw, extra)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    if not request_id:
        raise ValueError("request_id or video_url is required.")
    return get_generation_result(request_id, output_path=output_path, **kwargs)
