from ..._common import env_utils, http_utils
from ..post_processing import (
    build_result,
    download_audio,
    failure_result,
    first_audio_url,
    poll_until_ready,
    unavailable_cost,
)
from ..pre_processing import (
    add_if_present,
    endpoint_from_base,
    missing_endpoint_error,
    poll_options,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
)

PROVIDER = "topmediai"
ENV_NAME = "TOPMEDIAI_API_KEY"
DEFAULT_MODEL = "v4.5-plus"
COST_SOURCE = "unavailable"
GENERATE_PATH = "/v3/music/generate"
TASKS_PATH = "/v3/music/tasks"
BASE_URL = "https://api.topmediai.com"


def _selected_model(kwargs):
    """Return the selected TopMediai model version.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model version.
    """
    model = kwargs.pop("model", None)
    if model is not None and "mv" not in kwargs:
        kwargs["mv"] = model
    return kwargs.get("mv") or DEFAULT_MODEL


def _build_payload(model, prepared, kwargs):
    """Build the TopMediai music generation payload.

    Args:
        model: Required. TopMediai model version.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.

    Raises:
        RuntimeError: If action is missing.
    """
    action = kwargs.get("action")
    if not action:
        raise RuntimeError("action is required for TopMediai v3 generation.")

    payload = {
        "action": action,
        "style": kwargs.get("style") or prepared["prompt"],
        "mv": model,
    }
    add_if_present(
        payload,
        kwargs,
        "lyrics",
        "title",
        "instrumental",
        "gender",
        "continue_at",
        "continue_song_id",
        "audio_url",
        "singer_id",
    )
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable TopMediai cost metadata.

    Args:
        model: Required. TopMediai model version.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    credits = 3 if str(model).lower() in {"v4.5", "v4.5-plus", "v4.5 plus"} else 2
    return unavailable_cost(details={"credits_per_generation": credits, "model": model})


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate music with TopMediai.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path if a final URL is returned.
        sync: Optional. Pass `status_url` or `base_url` for task polling.
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
        endpoint = kwargs.get("endpoint_url") or endpoint_from_base(
            kwargs.get("base_url") or BASE_URL,
            GENERATE_PATH,
        )
        if not endpoint:
            raise missing_endpoint_error(PROVIDER, "the TopMediai API base URL")

        api_key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request_json(
            "POST",
            endpoint,
            headers={"x-api-key": api_key},
            json=payload,
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )
        audio_url = first_audio_url(response)
        task_id = _extract_task_id(response)
        if sync and task_id and not audio_url:
            poll_kwargs = dict(kwargs)
            poll_kwargs["model"] = model
            return poll_until_ready(
                lambda: get_generation_result(task_id, output_path=output_path, **poll_kwargs),
                **poll_options(kwargs),
            )
        saved_path = download_audio(
            audio_url,
            output_path,
            timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
        )
        status = "completed" if audio_url else "submitted"
        warnings = []
        if sync and not audio_url:
            warnings.append(
                "TopMediai polling requires status_url or base_url when the "
                "initial response does not include a final audio URL."
            )
        return build_result(
            PROVIDER,
            model=model,
            status=status,
            raw_response=response,
            request_id=task_id,
            audio_url=audio_url,
            output_path=saved_path,
            cost=_cost(model, kwargs),
            warnings=warnings,
            status_url=_status_url(task_id, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    """Fetch TopMediai status when the caller supplies a status URL.

    Args:
        request_id: Required. TopMediai task ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        status_url = _status_url(request_id, kwargs)
        if not status_url:
            raise missing_endpoint_error(
                PROVIDER,
                "a TopMediai status_url or exact task lookup contract",
            )
        api_key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request_json(
            "GET",
            status_url,
            headers={"x-api-key": api_key},
            params=kwargs.get("params") or {"ids": request_id},
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            request_id=request_id,
            cost=_cost(model, kwargs),
            status_url=status_url,
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, request_id=request_id)


def get_generation_result(request_id, output_path=None, **kwargs):
    """Fetch and optionally download a TopMediai result.

    Args:
        request_id: Required. TopMediai task ID.
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


def _status_url(task_id, kwargs):
    """Return a TopMediai status URL when safely available.

    Args:
        task_id: Optional. TopMediai task ID.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Status URL, or None.
    """
    if kwargs.get("status_url"):
        return str(kwargs["status_url"]).format(task_id=task_id, request_id=task_id)
    if task_id:
        return endpoint_from_base(kwargs.get("base_url") or BASE_URL, TASKS_PATH)
    return None


def _extract_task_id(response):
    """Extract a TopMediai task ID from a response.

    Args:
        response: Required. Provider response JSON.

    Returns:
        Task ID, or None.
    """
    if not isinstance(response, dict):
        return None
    for key in ("task_id", "taskId", "id", "music_id", "song_id"):
        if response.get(key):
            return response[key]
    data = response.get("data")
    if isinstance(data, dict):
        return _extract_task_id(data)
    return None
