import time

from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import (
    build_result,
    download_audio,
    estimated_cost,
    failure_result,
    first_audio_url,
    unavailable_cost,
)
from ..pre_processing import (
    add_if_present,
    endpoint_from_base,
    poll_settings,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "sonauto"
ENV_NAME = "SONAUTO_API_KEY"
DEFAULT_MODEL = "v3"
COST_SOURCE = "official_pricing_table"
BASE_URL = "https://api.sonauto.ai/v1"
GENERATE_PATH = "/generations/v3"
STATUS_PATH = "/generations/status/{task_id}"
RESULT_PATH = "/generations/{task_id}"
SUCCESS_STATUSES = {"success"}
FAILURE_STATUSES = {"failed", "failure", "error", "cancelled", "canceled"}


def _selected_model(kwargs):
    """Return the Sonauto generation version.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model or workflow version.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the Sonauto generations/v3 payload.

    Args:
        model: Required. Sonauto workflow version.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.
    """
    payload = {"prompt": prepared["prompt"]}
    add_if_present(
        payload,
        kwargs,
        "tags",
        "lyrics",
        "instrumental",
        "negative_tags",
        "prompt_strength",
        "style_scale",
        "length_range",
        "output_format",
        "output_bit_rate",
        "webhook_url",
        "enable_streaming",
        "stream_format",
        "audio_url",
        "audio_base64",
    )
    handled = set(payload) | {
        "cost_plan",
        "plan",
        "pricing_plan",
        "usd_per_100_credits",
        "credits",
    }
    payload.update(safe_payload_kwargs(kwargs, handled=handled))
    return payload


def _cost(model, kwargs):
    """Estimate Sonauto cost when a plan rate is supplied.

    Args:
        model: Required. Sonauto workflow version.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    credits = kwargs.get("credits")
    if credits is None:
        credits = 150 if kwargs.get("num_songs") == 2 else 100

    usd_per_100 = kwargs.get("usd_per_100_credits")
    if usd_per_100 is None:
        plan = str(
            kwargs.get("pricing_plan")
            or kwargs.get("cost_plan")
            or kwargs.get("plan")
            or ""
        ).strip().lower()
        rates = {
            "starter": 0.06,
            "pro": 0.06,
            "scale": 0.05,
            "enterprise": 0.04,
        }
        usd_per_100 = rates.get(plan)

    details = {
        "credits": credits,
        "model": model,
        "usd_per_100_credits": usd_per_100,
    }
    if usd_per_100 is None:
        return unavailable_cost(details=details)
    return estimated_cost((float(credits) / 100.0) * float(usd_per_100), COST_SOURCE, details)


def update_cost(result, **kwargs):
    """Refresh Sonauto cost metadata when pricing details are available.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    details = result.get("cost_details") if isinstance(result, dict) else {}
    model = result.get("model") if isinstance(result, dict) else None
    cost = _cost(model or DEFAULT_MODEL, details or {})
    if "cost_currency" not in cost:
        cost["cost_currency"] = "USD"
    return cost_utils.apply_cost_metadata(result, cost)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate music with Sonauto Melodia.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path when final audio is available.
        sync: Optional. Poll until completion when true.
        **kwargs: Optional. Provider-native generation parameters.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = None
    try:
        prepared = prepare_text_to_music(prompt, kwargs)
        model = _selected_model(kwargs)
        payload = _build_payload(model, prepared, kwargs)
        raw_response = _post_generation(payload, kwargs)
        task_id = raw_response.get("task_id") or raw_response.get("id")
        refs = _refs(task_id, kwargs)

        if not sync:
            return build_result(
                PROVIDER,
                model=model,
                status="submitted",
                raw_response=raw_response,
                request_id=task_id,
                cost=_cost(model, kwargs),
                **refs,
            )

        final_response = _poll_generation(task_id, kwargs)
        audio_url = first_audio_url(final_response)
        saved_path = download_audio(
            audio_url,
            output_path,
            timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
        )
        return build_result(
            PROVIDER,
            model=model,
            raw_response={"submit": raw_response, "result": final_response},
            request_id=task_id,
            audio_url=audio_url,
            output_path=saved_path,
            cost=_cost(model, kwargs),
            **refs,
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    """Fetch Sonauto generation status.

    Args:
        request_id: Required. Sonauto task ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        response = _get_json(_status_url(request_id, kwargs), kwargs)
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            request_id=request_id,
            cost=_cost(model, kwargs),
            **_refs(request_id, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, request_id=request_id)


def get_generation_result(request_id, output_path=None, **kwargs):
    """Fetch and optionally download a Sonauto generation result.

    Args:
        request_id: Required. Sonauto task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        response = _get_json(_result_url(request_id, kwargs), kwargs)
        audio_url = first_audio_url(response)
        saved_path = download_audio(audio_url, output_path, timeout=kwargs.get("download_timeout", 60))
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            request_id=request_id,
            audio_url=audio_url,
            output_path=saved_path,
            cost=_cost(model, kwargs),
            **_refs(request_id, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, request_id=request_id, output_path=output_path)


download_generation = get_generation_result


def _post_generation(payload, kwargs):
    """Submit a Sonauto generation task.

    Args:
        payload: Required. Request payload.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider response JSON.
    """
    return _request_json("POST", _generate_url(kwargs), kwargs, json=payload)


def _poll_generation(task_id, kwargs):
    """Poll Sonauto until the task succeeds.

    Args:
        task_id: Required. Sonauto task ID.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Final generation result response.
    """
    if not task_id:
        raise RuntimeError("Sonauto response did not include task_id.")

    interval, max_polls = poll_settings(kwargs, interval=10, max_polls=60)
    for _attempt in range(max_polls):
        status_response = _get_json(_status_url(task_id, kwargs), kwargs)
        status = _status_value(status_response)
        if status in SUCCESS_STATUSES:
            return _get_json(_result_url(task_id, kwargs), kwargs)
        if status in FAILURE_STATUSES:
            raise RuntimeError(f"Sonauto task failed with status '{status}'.")
        time.sleep(interval)
    raise TimeoutError("Sonauto task did not complete before max_polls.")


def _request_json(method, url, kwargs, json=None):
    """Send an authenticated Sonauto JSON request.

    Args:
        method: Required. HTTP method.
        url: Required. Request URL.
        kwargs: Required. Provider keyword arguments.
        json: Optional. JSON body.

    Returns:
        Provider response JSON.
    """
    api_key = env_utils.require_env_var(ENV_NAME)
    return http_utils.request_json(
        method,
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        json=json,
        timeout=request_timeout(kwargs),
        retries=request_retries(kwargs),
    )


def _get_json(url, kwargs):
    """Send an authenticated Sonauto GET request.

    Args:
        url: Required. Request URL.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider response JSON.
    """
    api_key = env_utils.require_env_var(ENV_NAME)
    response = http_utils.request(
        "GET",
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=request_timeout(kwargs),
        retries=request_retries(kwargs),
    )
    content_type = response.headers.get("content-type", "")
    if "json" in content_type.lower():
        return http_utils.response_json(response)
    text = response.text.strip()
    if text.startswith("{") or text.startswith("["):
        return http_utils.response_json(response)
    return {"status": text}


def _status_value(response):
    """Return a normalized Sonauto status from JSON or plain text.

    Args:
        response: Required. Status response.

    Returns:
        Lowercase status text.
    """
    if isinstance(response, dict):
        return str(response.get("status", "")).lower()
    return str(response).lower()


def _generate_url(kwargs):
    """Return the Sonauto generation URL.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        Generation URL.
    """
    return kwargs.get("endpoint_url") or endpoint_from_base(
        kwargs.get("base_url") or BASE_URL,
        GENERATE_PATH,
    )


def _status_url(task_id, kwargs):
    """Return the Sonauto status URL.

    Args:
        task_id: Required. Sonauto task ID.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Status URL.
    """
    if kwargs.get("status_url"):
        return str(kwargs["status_url"]).format(task_id=task_id)
    return endpoint_from_base(kwargs.get("base_url") or BASE_URL, STATUS_PATH.format(task_id=task_id))


def _result_url(task_id, kwargs):
    """Return the Sonauto result URL.

    Args:
        task_id: Required. Sonauto task ID.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Result URL.
    """
    if kwargs.get("result_url"):
        return str(kwargs["result_url"]).format(task_id=task_id)
    return endpoint_from_base(kwargs.get("base_url") or BASE_URL, RESULT_PATH.format(task_id=task_id))


def _refs(task_id, kwargs):
    """Return safe Sonauto async references.

    Args:
        task_id: Required. Sonauto task ID.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Async reference metadata.
    """
    if not task_id:
        return {}
    return {
        "status_url": _status_url(task_id, kwargs),
        "result_url": _result_url(task_id, kwargs),
    }
