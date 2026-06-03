from ..._common import cost_utils, env_utils, http_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "soundverse"
ENV_NAME = "SOUNDVERSE_API_KEY"
DEFAULT_MODEL = "music"
COST_SOURCE = "soundverse_billing"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    return pre_processing.compact_payload(dict(prepared))


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        source=COST_SOURCE,
        details={"endpoint": _endpoint_path(model, kwargs)},
    )


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(
        prompt,
        options,
        exclude=("endpoint",),
    )
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, options)

    try:
        response = http_utils.request_json(
            "POST",
            _endpoint(model, options, payload),
            headers=_headers(),
            json=payload,
            **pre_processing.http_options(options),
        )
        request_id = _message_id(response)
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

        final_response = _poll_message(request_id, response, options)
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
        response = http_utils.request_json(
            "GET",
            _status_url(request_id, options),
            headers=_headers(),
            **pre_processing.http_options(options),
        )
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


def _poll_message(request_id, response, kwargs):
    if not request_id:
        return response
    return post_processing.poll_until_ready(
        lambda: http_utils.request_json(
            "GET",
            _status_url(request_id, kwargs),
            headers=_headers(),
            **pre_processing.http_options(kwargs),
        ),
        **pre_processing.poll_options(kwargs),
    )


def _headers():
    key = env_utils.require_env_var(ENV_NAME)
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _endpoint(model, kwargs, payload):
    endpoint_url = kwargs.get("endpoint_url")
    if endpoint_url:
        return endpoint_url
    return f"{_base_url(kwargs)}{_endpoint_path(model, kwargs, payload)}"


def _endpoint_path(model, kwargs, payload=None):
    if kwargs.get("endpoint"):
        endpoint = kwargs["endpoint"]
        return endpoint if str(endpoint).startswith("/") else f"/{endpoint}"

    normalized = str(model).lower().strip("/")
    if normalized in ("song", "generate/song") or (payload or {}).get("lyrics"):
        return "/v5/generate/song"
    if normalized in ("song_sync", "generate/song/sync"):
        return "/v5/generate/song/sync"
    if normalized in ("music_sync", "generate/music/sync", "sync"):
        return "/v5/generate/music/sync"
    return "/v5/generate/music"


def _base_url(kwargs):
    return kwargs.get("base_url", "https://api.soundverse.ai").rstrip("/")


def _status_url(request_id, kwargs):
    return kwargs.get("status_url") or f"{_base_url(kwargs)}/v5/status?message_id={request_id}"


def _refs(request_id, kwargs):
    if not request_id:
        return {}
    url = _status_url(request_id, kwargs)
    return {
        "status_url": url,
        "result_url": url,
    }


def _message_id(response):
    return (
        response.get("message_id")
        or response.get("messageId")
        or response.get("id")
        or result_utils.extract_request_id(response)
    )


def _failure(model, exc, request_id=None, output_path=None):
    return result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
    )
