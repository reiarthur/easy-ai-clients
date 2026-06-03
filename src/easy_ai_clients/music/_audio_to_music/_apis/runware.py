from uuid import uuid4

from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "runware"
ENV_NAME = "RUNWARE_API_KEY"
DEFAULT_MODEL = "runware:ace-step@v1.5-turbo"
DEFAULT_ENDPOINT = "https://api.runware.ai/v1"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit a Runware audioInference task."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    raw_response = http_utils.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        json=[payload],
        timeout=timeout,
        retries=retries,
    )
    cost = _cost(model=model, payload=raw_response)
    if not cost_utils.has_available_cost(cost):
        cost = _cost(model=model, payload=payload)
    request_id = payload.get("taskUUID")
    async_delivery = payload.get("deliveryMethod") == "async"
    if not sync or async_delivery:
        return build_result(
            PROVIDER,
            model,
            raw_response,
            output_path=output_path,
            status="submitted",
            request_id=request_id,
            provider_metadata={"taskUUID": request_id},
            cost=cost,
        )

    return build_result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        request_id=request_id,
        provider_metadata={"taskUUID": request_id},
        cost=cost,
    )


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch Runware async response by task UUID."""
    return get_generation_result(request_id, model=model, **kwargs)


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch Runware async response by task UUID."""
    endpoint = kwargs.get("endpoint", DEFAULT_ENDPOINT)
    task = {
        "taskType": "getResponse",
        "taskUUID": request_id,
    }
    response = http_utils.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        json=[task],
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )
    return build_result(PROVIDER, model or DEFAULT_MODEL, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the Runware audioInference task."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    payload.setdefault("taskType", "audioInference")
    payload.setdefault("taskUUID", str(uuid4()))
    payload.setdefault("model", model or DEFAULT_MODEL)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "positivePrompt"))
    inputs = dict(payload.pop("inputs", {}) or {})
    apply_audio_reference(
        inputs,
        audio,
        url_field=kwargs.get("url_field", "audio"),
        data_uri_field=kwargs.get("data_uri_field", "audio"),
        file_id_field=kwargs.get("file_id_field", "audio"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    payload["inputs"] = inputs
    settings = dict(payload.pop("settings", {}) or {})
    for key in ("lyrics", "instrumental", "lyricsOptimizer", "bpm", "keyScale",
                "timeSignature", "vocalLanguage"):
        payload.pop(key, None)
        if key in kwargs and key not in settings:
            settings[key] = kwargs[key]
    if settings:
        payload["settings"] = settings
    return payload


def _cost(model=None, payload=None, **kwargs):
    """Return Runware cost metadata when the provider response includes it."""
    payload = payload or {}
    response_cost = cost_utils.cost_from_response(payload)
    if cost_utils.has_available_cost(response_cost):
        return response_cost

    return cost_utils.unavailable_cost_metadata(
        details={"model": model, **kwargs},
    )


def update_cost(result, **kwargs):
    """Refresh Runware cost metadata from response data or documented pricing.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Ignored except for dispatcher compatibility.

    Returns:
        The updated result dictionary.
    """
    raw_response = result.get("raw_response") if isinstance(result, dict) else result
    model = result.get("model") if isinstance(result, dict) else None
    details = result.get("cost_details") if isinstance(result, dict) else {}
    cost = _cost(model or DEFAULT_MODEL, raw_response or details or {})
    return cost_utils.apply_cost_metadata(result, cost)


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": f"Bearer {api_key}"}
