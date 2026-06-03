from ..._common import cost_utils, env_utils, http_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "musicful"
ENV_NAME = "MUSICFUL_API_KEY"
DEFAULT_MODEL = "MFV3.0"
COST_SOURCE = "musicful_account_billing"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    payload = dict(prepared)
    if "style" in payload:
        payload.pop("prompt", None)
    elif payload.get("prompt"):
        payload["style"] = payload.pop("prompt")
    payload.setdefault("action", "auto")
    payload.setdefault("mv", model)
    if isinstance(payload.get("instrumental"), bool):
        payload["instrumental"] = int(payload["instrumental"])
    return pre_processing.compact_payload(payload)


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        source=COST_SOURCE,
        details={
            "action": kwargs.get("action"),
            "mv": model,
        },
    )


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(prompt, options)
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, payload)

    try:
        response = http_utils.request_json(
            "POST",
            f"{_base_url(options)}/music/generate",
            headers=_headers(),
            json=payload,
            **pre_processing.http_options(options),
        )
        request_id = _task_id(response)
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
    return http_utils.request_json(
        "GET",
        kwargs.get("status_url") or f"{_base_url(kwargs)}/music/tasks",
        headers=_headers(),
        params={"ids": request_id},
        **pre_processing.http_options(kwargs),
    )


def _headers():
    key = env_utils.require_env_var(ENV_NAME)
    return {
        "x-api-key": key,
        "Content-Type": "application/json",
    }


def _base_url(kwargs):
    return kwargs.get("base_url", "https://api.musicful.ai/v1").rstrip("/")


def _refs(request_id, kwargs):
    if not request_id:
        return {}
    return {
        "status_url": kwargs.get("status_url") or f"{_base_url(kwargs)}/music/tasks",
    }


def _task_id(response):
    return (
        response.get("task_id")
        or response.get("taskId")
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
