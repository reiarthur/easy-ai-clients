from ..._common import cost_utils, env_utils, http_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "falai"
ENV_NAME = "FAL_KEY"
DEFAULT_MODEL = "fal-ai/minimax-music/v2.6"
COST_SOURCE = "fal_model_pricing"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    payload = dict(prepared)
    return pre_processing.compact_payload(payload)


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        source=COST_SOURCE,
        details={"model": model},
    )


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(
        prompt,
        options,
        exclude=("fal_request_timeout", "x_fal_request_timeout", "fal_no_retry"),
    )
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, payload)

    try:
        headers = _headers(options)
        response = http_utils.request_json(
            "POST",
            _queue_url(model, options),
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

        final_response = _poll_or_fetch_result(response, headers, options)
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
            options.get("status_url") or _request_url(model, request_id, "status", options),
            headers=_headers(options),
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
            options.get("response_url") or _request_url(model, request_id, "response", options),
            headers=_headers(options),
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


def _poll_or_fetch_result(response, headers, kwargs):
    status_url = response.get("status_url")
    response_url = response.get("response_url")

    if status_url:
        latest = post_processing.poll_until_ready(
            lambda: http_utils.request_json(
                "GET",
                status_url,
                headers=headers,
                **pre_processing.http_options(kwargs),
            ),
            **pre_processing.poll_options(kwargs),
        )
        if _is_completed(latest) and response_url:
            return http_utils.request_json(
                "GET",
                response_url,
                headers=headers,
                **pre_processing.http_options(kwargs),
            )
        return latest

    if response_url:
        return http_utils.request_json(
            "GET",
            response_url,
            headers=headers,
            **pre_processing.http_options(kwargs),
        )
    return response


def _headers(kwargs):
    key = env_utils.require_env_var(ENV_NAME)
    headers = {
        "Authorization": f"Key {key}",
        "Content-Type": "application/json",
    }
    timeout = kwargs.get("fal_request_timeout") or kwargs.get("x_fal_request_timeout")
    if timeout:
        headers["X-Fal-Request-Timeout"] = str(timeout)
    if kwargs.get("fal_no_retry"):
        headers["X-Fal-No-Retry"] = "1"
    return headers


def _queue_url(model, kwargs):
    return f"{kwargs.get('base_url', 'https://queue.fal.run').rstrip('/')}/{model.strip('/')}"


def _request_url(model, request_id, suffix, kwargs):
    return f"{_queue_url(model, kwargs)}/requests/{request_id}/{suffix}"


def _refs(response):
    return {
        "status_url": response.get("status_url"),
        "response_url": response.get("response_url"),
    }


def _is_completed(response):
    status = result_utils.extract_status(response)
    return str(status).strip().lower() in post_processing.COMPLETED_STATUSES


def _failure(model, exc, request_id=None, output_path=None):
    return result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
    )
