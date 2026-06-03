from ..._common import cost_utils, env_utils, http_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "replicate"
ENV_NAME = "REPLICATE_API_TOKEN"
DEFAULT_MODEL = "minimax/music-2.6"
COST_SOURCE = "unavailable"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    input_payload = dict(prepared)
    payload = {"input": input_payload}

    version = kwargs.get("version")
    if version:
        payload["version"] = version

    for key in ("webhook", "webhook_events_filter"):
        if kwargs.get(key) is not None:
            payload[key] = kwargs[key]

    return pre_processing.compact_payload(payload)


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        details={"model": model},
    )


def update_cost(result, **kwargs):
    """Refresh Replicate cost metadata from documented output pricing.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    model = result.get("model") if isinstance(result, dict) else None
    details = result.get("cost_details") if isinstance(result, dict) else {}
    cost = _cost(model or DEFAULT_MODEL, details or {})
    return cost_utils.apply_cost_metadata(result, cost)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(
        prompt,
        options,
        exclude=("version", "webhook", "webhook_events_filter"),
    )
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, prepared)

    try:
        headers = _headers(sync, options)
        response = http_utils.request_json(
            "POST",
            _prediction_url(model, options),
            headers=headers,
            json=payload,
            **pre_processing.http_options(options),
        )
        refs = _refs(response)
        if not sync or post_processing.collect_audio_candidates(response):
            return post_processing.normalize_response(
                PROVIDER,
                model,
                response,
                output_path=output_path,
                cost=cost,
                status=None if post_processing.collect_audio_candidates(response) else "submitted",
                refs=refs,
                download_timeout=options.get("download_timeout", 60),
            )

        final_response = _poll_prediction(response, headers, options)
        return post_processing.normalize_response(
            PROVIDER,
            model,
            final_response,
            output_path=output_path,
            cost=cost,
            refs=refs or _refs(final_response),
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    try:
        response = http_utils.request_json(
            "GET",
            options.get("status_url") or _prediction_get_url(request_id, options),
            headers=_headers(False, options),
            **pre_processing.http_options(options),
        )
        return post_processing.normalize_response(PROVIDER, model, response)
    except Exception as exc:
        return _failure(model, exc, request_id=request_id)


def get_generation_result(request_id, **kwargs):
    options = dict(kwargs)
    output_path = options.get("output_path")
    model = _selected_model(options)
    try:
        response = http_utils.request_json(
            "GET",
            options.get("result_url") or _prediction_get_url(request_id, options),
            headers=_headers(False, options),
            **pre_processing.http_options(options),
        )
        return post_processing.normalize_response(
            PROVIDER,
            model,
            response,
            output_path=output_path,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, request_id=request_id, output_path=output_path)


def _poll_prediction(response, headers, kwargs):
    get_url = response.get("urls", {}).get("get") if isinstance(response.get("urls"), dict) else None
    get_url = get_url or response.get("status_url")
    if not get_url:
        return response
    return post_processing.poll_until_ready(
        lambda: http_utils.request_json(
            "GET",
            get_url,
            headers=headers,
            **pre_processing.http_options(kwargs),
        ),
        **pre_processing.poll_options(kwargs),
    )


def _headers(sync, kwargs):
    key = env_utils.require_env_var(ENV_NAME)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if sync and kwargs.get("prefer_wait", True):
        headers["Prefer"] = "wait"
    return headers


def _prediction_url(model, kwargs):
    if kwargs.get("endpoint_url"):
        return kwargs["endpoint_url"]

    base_url = kwargs.get("base_url", "https://api.replicate.com").rstrip("/")
    if kwargs.get("version") or "/" not in str(model):
        return f"{base_url}/v1/predictions"
    return f"{base_url}/v1/models/{str(model).strip('/')}/predictions"


def _prediction_get_url(request_id, kwargs):
    base_url = kwargs.get("base_url", "https://api.replicate.com").rstrip("/")
    return f"{base_url}/v1/predictions/{request_id}"


def _refs(response):
    urls = response.get("urls") if isinstance(response, dict) else None
    if not isinstance(urls, dict):
        return {}
    return {
        "status_url": urls.get("get"),
        "result_url": urls.get("get"),
        "operation_url": urls.get("cancel"),
    }


def _failure(model, exc, request_id=None, output_path=None):
    return result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
    )
