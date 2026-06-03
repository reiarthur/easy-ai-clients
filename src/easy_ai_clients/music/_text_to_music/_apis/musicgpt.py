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
    poll_options,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "musicgpt"
ENV_NAME = "MUSICGPT_API_KEY"
DEFAULT_MODEL = None
COST_SOURCE = "unavailable"
ENDPOINT = "https://api.musicgpt.com/api/public/v1/MusicAI"
STATUS_ENDPOINT = "https://api.musicgpt.com/api/public/v1/byId"


def _selected_model(kwargs):
    """Return the selected MusicGPT model or mode.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model, if provided.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the MusicGPT MusicAI payload.

    Args:
        model: Optional. MusicGPT model or mode.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.
    """
    payload = {"prompt": prepared["prompt"]}
    if model:
        payload["model"] = model
    add_if_present(
        payload,
        kwargs,
        "lyrics",
        "music_style",
        "make_instrumental",
        "vocal_only",
        "output_length",
        "webhook_url",
        "gender",
        "voice_id",
    )
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable MusicGPT cost metadata.

    Args:
        model: Optional. MusicGPT model or mode.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate music with MusicGPT.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path if a final URL is returned.
        sync: Optional. MusicGPT is async; pass `status_url` for local polling.
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
        api_key = env_utils.require_env_var(ENV_NAME)
        endpoint = kwargs.get("endpoint_url") or ENDPOINT
        response = http_utils.request_json(
            "POST",
            endpoint,
            headers={"Authorization": api_key},
            json=payload,
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )
        audio_url = first_audio_url(response)
        task_id = _extract_task_id(response)
        saved_path = download_audio(
            audio_url,
            output_path,
            timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
        )
        status = "completed" if audio_url else "submitted"
        if sync and task_id and not audio_url:
            poll_kwargs = dict(kwargs)
            poll_kwargs["model"] = model
            return poll_until_ready(
                lambda: get_generation_result(task_id, output_path=output_path, **poll_kwargs),
                **poll_options(kwargs),
            )
        warnings = []
        if sync and not audio_url:
            warnings.append(
                "MusicGPT status polling requires status_url when the initial "
                "response does not include a final audio URL."
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
            status_url=kwargs.get("status_url"),
            result_url=kwargs.get("result_url"),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    """Fetch MusicGPT status when the caller supplies a status URL.

    Args:
        request_id: Required. MusicGPT task ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        status_url = kwargs.get("status_url")
        status_url = status_url or STATUS_ENDPOINT
        api_key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request_json(
            "GET",
            str(status_url).format(task_id=request_id, request_id=request_id),
            headers={"Authorization": api_key},
            params=kwargs.get("params") or {
                "conversionType": "MUSIC_AI",
                "task_id": request_id,
            },
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
    """Fetch and optionally download a MusicGPT result.

    Args:
        request_id: Required. MusicGPT task ID.
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


def _extract_task_id(response):
    """Extract a MusicGPT task ID from a response.

    Args:
        response: Required. Provider response JSON.

    Returns:
        Task ID, or None.
    """
    if not isinstance(response, dict):
        return None
    for key in ("task_id", "taskId", "id", "music_id", "conversion_id"):
        if response.get(key):
            return response[key]
    data = response.get("data")
    if isinstance(data, dict):
        return _extract_task_id(data)
    return None
