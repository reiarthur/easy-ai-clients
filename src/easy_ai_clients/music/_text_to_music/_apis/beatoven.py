import time

from ..._common import env_utils, http_utils
from ..post_processing import (
    build_result,
    download_audio,
    failure_result,
    first_audio_url,
    unavailable_cost,
)
from ..pre_processing import (
    add_if_present,
    endpoint_from_base,
    missing_endpoint_error,
    poll_settings,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "beatoven"
ENV_NAME = "BEATOVEN_API_KEY"
DEFAULT_MODEL = "maestro"
COST_SOURCE = "unavailable"
STATUS_PATH = "/api/v1/tasks/{task_id}"


def _selected_model(kwargs):
    """Return the Beatoven model.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the Beatoven composition payload.

    Args:
        model: Required. Beatoven model.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.
    """
    payload = {"prompt": {"text": prepared["prompt"]}}
    if model:
        payload["model"] = model
    add_if_present(payload, kwargs, "format", "looping")
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable Beatoven cost metadata.

    Args:
        model: Required. Beatoven model.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate background music with Beatoven.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path when a final URL is available.
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
        endpoint = kwargs.get("endpoint_url")
        if not endpoint:
            raise missing_endpoint_error(
                PROVIDER,
                "the Beatoven composition submit endpoint URL",
            )

        raw_response = _post_task(endpoint, payload, kwargs)
        task_id = raw_response.get("task_id") or raw_response.get("id")
        status_url = _status_url(kwargs, task_id)
        if not sync:
            return build_result(
                PROVIDER,
                model=model,
                status="submitted",
                raw_response=raw_response,
                request_id=task_id,
                cost=_cost(model, kwargs),
                status_url=status_url,
            )

        final_response = _poll_task(task_id, kwargs, raw_response=raw_response)
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
            status_url=status_url,
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    """Fetch Beatoven task status.

    Args:
        request_id: Required. Beatoven task ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        response = _get_task(request_id, kwargs)
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            request_id=request_id,
            cost=_cost(model, kwargs),
            status_url=_status_url(kwargs, request_id),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, request_id=request_id)


def get_generation_result(request_id, output_path=None, **kwargs):
    """Fetch and optionally download a completed Beatoven task result.

    Args:
        request_id: Required. Beatoven task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    result = get_generation_status(request_id, **kwargs)
    audio_url = first_audio_url(result.get("raw_response"))
    saved_path = download_audio(audio_url, output_path, timeout=kwargs.get("download_timeout", 60))
    result["audio_url"] = audio_url
    result["music_url"] = audio_url
    result["output_path"] = saved_path
    return result


download_generation = get_generation_result


def _post_task(endpoint, payload, kwargs):
    """Create a Beatoven task.

    Args:
        endpoint: Required. Submit endpoint.
        payload: Required. Request payload.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider response JSON.
    """
    api_key = env_utils.require_env_var(ENV_NAME)
    return http_utils.request_json(
        "POST",
        endpoint,
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=request_timeout(kwargs),
        retries=request_retries(kwargs),
    )


def _get_task(task_id, kwargs):
    """Fetch a Beatoven task.

    Args:
        task_id: Required. Beatoven task ID.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider response JSON.
    """
    status_url = _status_url(kwargs, task_id)
    if not status_url:
        raise missing_endpoint_error(
            PROVIDER,
            "a Beatoven base URL or status_url for task polling",
        )
    api_key = env_utils.require_env_var(ENV_NAME)
    return http_utils.request_json(
        "GET",
        status_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=request_timeout(kwargs),
        retries=request_retries(kwargs),
    )


def _poll_task(task_id, kwargs, raw_response=None):
    """Poll a Beatoven task until it is composed.

    Args:
        task_id: Required. Beatoven task ID.
        kwargs: Required. Provider keyword arguments.
        raw_response: Optional. Submit response.

    Returns:
        Final provider response JSON.
    """
    if not task_id:
        raise RuntimeError("Beatoven response did not include task_id.")

    interval, max_polls = poll_settings(kwargs)
    response = raw_response or {}
    for _attempt in range(max_polls):
        response = _get_task(task_id, kwargs)
        status = str(response.get("status", "")).lower()
        if status == "composed" or first_audio_url(response):
            return response
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise RuntimeError(f"Beatoven task failed with status '{status}'.")
        time.sleep(interval)
    raise TimeoutError("Beatoven task did not complete before max_polls.")


def _status_url(kwargs, task_id):
    """Build a Beatoven task status URL.

    Args:
        kwargs: Required. Provider keyword arguments.
        task_id: Required. Beatoven task ID.

    Returns:
        Status URL, or None.
    """
    if kwargs.get("status_url"):
        return str(kwargs["status_url"]).format(task_id=task_id)
    return endpoint_from_base(kwargs.get("base_url"), STATUS_PATH.format(task_id=task_id))
