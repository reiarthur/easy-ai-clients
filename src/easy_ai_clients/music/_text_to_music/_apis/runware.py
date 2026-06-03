import uuid

from ..._common import cost_utils, env_utils, http_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "runware"
ENV_NAME = "RUNWARE_API_KEY"
DEFAULT_MODEL = "minimax:music@2.6"
COST_SOURCE = "runware_response"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    payload = {
        "taskType": "audioInference",
        "taskUUID": prepared.get("taskUUID") or prepared.get("task_uuid") or str(uuid.uuid4()),
        "model": model,
        "positivePrompt": prepared.get("positivePrompt") or prepared.get("positive_prompt") or prepared.get("prompt"),
    }

    settings = dict(prepared.get("settings") or {})
    for source, target in (
        ("lyrics", "lyrics"),
        ("instrumental", "instrumental"),
        ("lyricsOptimizer", "lyricsOptimizer"),
        ("lyrics_optimizer", "lyricsOptimizer"),
        ("bpm", "bpm"),
        ("keyScale", "keyScale"),
        ("keyscale", "keyScale"),
        ("timeSignature", "timeSignature"),
        ("timesignature", "timeSignature"),
        ("vocalLanguage", "vocalLanguage"),
        ("vocal_language", "vocalLanguage"),
    ):
        if prepared.get(source) is not None:
            settings[target] = prepared[source]

    inputs = dict(prepared.get("inputs") or {})
    if prepared.get("audio") is not None:
        inputs["audio"] = prepared["audio"]

    for key in (
        "negativePrompt",
        "negative_prompt",
        "seed",
        "numberResults",
        "number_results",
        "outputType",
        "output_type",
        "outputFormat",
        "output_format",
        "audioSettings",
        "audio_settings",
        "webhookURL",
        "webhook_url",
        "deliveryMethod",
        "delivery_method",
        "uploadEndpoint",
        "upload_endpoint",
        "ttl",
        "includeCost",
        "include_cost",
        "repaintingStart",
        "repainting_start",
        "repaintingEnd",
        "repainting_end",
    ):
        if prepared.get(key) is not None:
            payload[_camel_runware_key(key)] = prepared[key]

    if settings:
        payload["settings"] = settings
    if inputs:
        payload["inputs"] = inputs

    return pre_processing.compact_payload(payload)


def _cost(model, kwargs):
    response_cost = cost_utils.cost_from_response(kwargs)
    if cost_utils.has_available_cost(response_cost):
        return response_cost

    return cost_utils.unavailable_cost_metadata(
        details={"model": model},
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


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    if not sync:
        options.setdefault("deliveryMethod", "async")

    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(prompt, options)
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, payload)

    try:
        response = http_utils.request_json(
            "POST",
            _endpoint(options),
            headers=_headers(),
            json=[payload],
            **pre_processing.http_options(options),
        )
        response_cost = _cost(model, response)
        if cost_utils.has_available_cost(response_cost):
            cost = response_cost
        request_id = payload["taskUUID"]
        refs = _refs(request_id, options)
        if not sync or post_processing.collect_audio_candidates(response):
            return post_processing.normalize_response(
                PROVIDER,
                model,
                response,
                output_path=output_path,
                cost=cost,
                status=None if post_processing.collect_audio_candidates(response) else "submitted",
                refs=refs,
                request_id=request_id,
                download_timeout=options.get("download_timeout", 60),
            )

        final_response = _poll_task(request_id, response, options)
        response_cost = _cost(model, final_response)
        if cost_utils.has_available_cost(response_cost):
            cost = response_cost
        return post_processing.normalize_response(
            PROVIDER,
            model,
            final_response,
            output_path=output_path,
            cost=cost,
            refs=refs,
            request_id=request_id,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    return get_generation_result(request_id, **kwargs)


def get_generation_result(request_id, **kwargs):
    options = dict(kwargs)
    output_path = options.get("output_path")
    model = _selected_model(options)
    try:
        response = _fetch_task(request_id, options)
        return post_processing.normalize_response(
            PROVIDER,
            model,
            response,
            output_path=output_path,
            refs=_refs(request_id, options),
            request_id=request_id,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, request_id=request_id, output_path=output_path)


def _poll_task(request_id, response, kwargs):
    if not request_id:
        return response
    return post_processing.poll_until_ready(
        lambda: _fetch_task(request_id, kwargs),
        **pre_processing.poll_options(kwargs),
    )


def _fetch_task(request_id, kwargs):
    payload = {
        "taskType": "getResponse",
        "taskUUID": request_id,
    }
    return http_utils.request_json(
        "POST",
        _endpoint(kwargs),
        headers=_headers(),
        json=[payload],
        **pre_processing.http_options(kwargs),
    )


def _headers():
    key = env_utils.require_env_var(ENV_NAME)
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _endpoint(kwargs):
    return kwargs.get("endpoint_url") or kwargs.get("base_url", "https://api.runware.ai/v1").rstrip("/")


def _refs(request_id, kwargs):
    if not request_id:
        return {}
    return {
        "status_url": kwargs.get("status_url") or _endpoint(kwargs),
    }


def _camel_runware_key(key):
    mapping = {
        "negative_prompt": "negativePrompt",
        "number_results": "numberResults",
        "output_type": "outputType",
        "output_format": "outputFormat",
        "audio_settings": "audioSettings",
        "webhook_url": "webhookURL",
        "delivery_method": "deliveryMethod",
        "upload_endpoint": "uploadEndpoint",
        "include_cost": "includeCost",
        "repainting_start": "repaintingStart",
        "repainting_end": "repaintingEnd",
    }
    return mapping.get(key, key)


def _failure(model, exc, request_id=None, output_path=None):
    return result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
    )
