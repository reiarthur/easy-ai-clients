"""Runway custom avatar creation wrapper."""

from ..._shared import normalize_result, require_env, runway_media_uri, runway_submit

PROVIDER = "runway"
ENV_NAME = "RUNWAYML_API_SECRET"
DEFAULT_MODEL = "gwm1_avatars"
COMMON_OPTIONS = {"timeout_seconds", "extra_payload"}


def _voice_object(voice):
    if isinstance(voice, dict):
        normalized = dict(voice)
        if "preset_id" in normalized and "presetId" not in normalized:
            normalized["presetId"] = normalized.pop("preset_id")
        return normalized
    if isinstance(voice, str) and voice.strip():
        return {"type": "runway-live-preset", "presetId": voice.strip()}
    raise ValueError("Runway create_avatar requires voice as a preset id or provider voice object.")


def _build_payload(reference_image, name, voice, kwargs):
    if not name or not str(name).strip():
        raise ValueError("Runway create_avatar requires name.")
    payload = {
        "name": str(name).strip(),
        "referenceImage": reference_image,
        "voice": _voice_object(voice),
    }
    if kwargs.get("personality") is not None:
        payload["personality"] = kwargs["personality"]
    for name, value in kwargs.items():
        if name not in COMMON_OPTIONS and name not in {"personality"} and name not in payload and value is not None:
            payload[name] = value
    if "extra_payload" in kwargs:
        from ..._shared import merge_extra_payload

        payload = merge_extra_payload(payload, kwargs)
    return payload


def _avatar_id(raw):
    avatar_id = raw.get("id") or raw.get("avatarId") or raw.get("avatar_id")
    if not avatar_id:
        raise RuntimeError("Runway avatar creation did not return an avatar id.")
    return avatar_id


def create_avatar(
    image_path=None,
    image_url=None,
    name=None,
    voice=None,
    **kwargs,
):
    api_key = require_env(ENV_NAME, "Runway")
    reference_image = runway_media_uri(
        image_path,
        image_url,
        "image_path",
        "image_url",
        api_key,
        timeout_seconds=kwargs.get("timeout_seconds"),
    )
    if not reference_image:
        raise ValueError("Runway create_avatar requires image, image_path, or image_url.")
    payload = _build_payload(reference_image, name, voice, kwargs)
    raw = runway_submit("/v1/avatars", payload, api_key, timeout_seconds=kwargs.get("timeout_seconds"))
    avatar_id = _avatar_id(raw)
    extra = {
        "avatar_id": avatar_id,
        "cost_reason": "Runway avatar creation pricing is not exposed as per-request USD in the public API response.",
    }
    return normalize_result(
        PROVIDER,
        DEFAULT_MODEL,
        "submitted" if str(raw.get("status", "")).upper() == "PROCESSING" else "completed",
        avatar_id,
        None,
        None,
        0.0,
        True,
        "unavailable",
        raw,
        extra,
    )
