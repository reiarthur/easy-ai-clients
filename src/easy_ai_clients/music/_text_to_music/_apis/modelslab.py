import time

from ..._common import env_utils, http_utils, media_utils
from ..post_processing import build_result, download_audio, failure_result, unavailable_cost
from ..pre_processing import (
    add_if_present,
    poll_settings,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "modelslab"
ENV_NAME = "MODELSLAB_API_KEY"
DEFAULT_MODEL = None
COST_SOURCE = "unavailable"
ENDPOINT = "https://modelslab.com/api/v6/voice/music_gen"
PROCESSING_STATUSES = {"processing", "queued"}
FAILURE_STATUSES = {"failed", "failure", "error", "cancelled", "canceled"}


def _selected_model(kwargs):
    """Return the selected ModelsLab model, if provided.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model, if provided.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the ModelsLab MusicGen payload.

    Args:
        model: Optional. ModelsLab model.
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
        "init_audio",
        "duration",
        "output_format",
        "base64",
        "temp",
        "webhook",
        "track_id",
    )
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable ModelsLab cost metadata.

    Args:
        model: Optional. ModelsLab model.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate instrumental music with ModelsLab MusicGen.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path when final audio is available.
        sync: Optional. Poll only when the response exposes a fetch URL.
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
        payload["key"] = env_utils.require_env_var(ENV_NAME)
        endpoint = kwargs.get("endpoint_url") or ENDPOINT
        response = http_utils.request_json(
            "POST",
            endpoint,
            json=payload,
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )

        audio_url = _output_url(response)
        if audio_url:
            saved_path = download_audio(
                audio_url,
                output_path,
                timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
            )
            return build_result(
                PROVIDER,
                model=model,
                status="completed",
                raw_response=response,
                audio_url=audio_url,
                output_path=saved_path,
                cost=_cost(model, kwargs),
                result_url=_fetch_url(response),
            )

        request_id = _request_id(response)
        fetch_url = _fetch_url(response)
        status = str(response.get("status", "")).lower() if isinstance(response, dict) else ""
        if sync and fetch_url and status in PROCESSING_STATUSES:
            final_response = _poll_fetch_result(fetch_url, kwargs)
            audio_url = _output_url(final_response)
            saved_path = download_audio(
                audio_url,
                output_path,
                timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
            )
            return build_result(
                PROVIDER,
                model=model,
                raw_response={"submit": response, "result": final_response},
                request_id=request_id,
                audio_url=audio_url,
                output_path=saved_path,
                cost=_cost(model, kwargs),
                result_url=fetch_url,
            )

        warnings = []
        if sync and status in PROCESSING_STATUSES and not fetch_url:
            warnings.append(
                "ModelsLab polling requires a concrete result URL when the "
                "provider response does not include one."
            )
        return build_result(
            PROVIDER,
            model=model,
            status="submitted",
            raw_response=response,
            request_id=request_id,
            cost=_cost(model, kwargs),
            warnings=warnings,
            result_url=fetch_url,
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    """Fetch ModelsLab status when a result URL is supplied.

    Args:
        request_id: Required. Provider job ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        result_url = kwargs.get("result_url") or kwargs.get("status_url")
        if not result_url:
            raise RuntimeError(
                "ModelsLab status polling requires result_url or status_url."
            )
        response = _fetch_result(
            str(result_url).format(request_id=request_id, task_id=request_id),
            kwargs,
        )
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            request_id=request_id,
            cost=_cost(model, kwargs),
            result_url=result_url,
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, request_id=request_id)


def get_generation_result(request_id, output_path=None, **kwargs):
    """Fetch and optionally download a ModelsLab result.

    Args:
        request_id: Required. Provider job ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    result = get_generation_status(request_id, **kwargs)
    audio_url = _output_url(result.get("raw_response"))
    saved_path = download_audio(audio_url, output_path, timeout=kwargs.get("download_timeout", 60))
    result["audio_url"] = audio_url
    result["music_url"] = audio_url
    result["output_path"] = saved_path
    return result


download_generation = get_generation_result


def _poll_fetch_result(fetch_url, kwargs):
    """Poll a ModelsLab fetch result URL.

    Args:
        fetch_url: Required. Result polling URL from the provider response.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Final provider response JSON.
    """
    interval, max_polls = poll_settings(kwargs, interval=10, max_polls=60)
    for _attempt in range(max_polls):
        response = _fetch_result(fetch_url, kwargs)
        if _output_url(response):
            return response
        status = str(response.get("status", "")).lower() if isinstance(response, dict) else ""
        if status in FAILURE_STATUSES:
            raise RuntimeError(f"ModelsLab task failed with status '{status}'.")
        time.sleep(interval)
    raise TimeoutError("ModelsLab task did not complete before max_polls.")


def _fetch_result(fetch_url, kwargs):
    """Fetch a ModelsLab queued result with the documented POST body.

    Args:
        fetch_url: Required. Fetch URL.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider response JSON.
    """
    return http_utils.request_json(
        "POST",
        fetch_url,
        json={"key": env_utils.require_env_var(ENV_NAME)},
        timeout=request_timeout(kwargs),
        retries=request_retries(kwargs),
    )


def _output_url(response):
    """Extract the first final output URL from a ModelsLab response.

    Args:
        response: Required. Provider response JSON.

    Returns:
        Output URL, or None.
    """
    if not isinstance(response, dict):
        return None
    output = response.get("output")
    if output is None and isinstance(response.get("data"), dict):
        output = response["data"].get("output")
    if isinstance(output, str) and media_utils.is_remote_url(output):
        return output
    if isinstance(output, list | tuple):
        for item in output:
            if isinstance(item, str) and media_utils.is_remote_url(item):
                return item
            if isinstance(item, dict):
                nested = _output_url({"output": item.get("url") or item.get("file_url")})
                if nested:
                    return nested
    return None


def _fetch_url(response):
    """Extract a ModelsLab fetch result URL if present.

    Args:
        response: Required. Provider response JSON.

    Returns:
        Fetch URL, or None.
    """
    if not isinstance(response, dict):
        return None
    for key in ("fetch_result", "fetchResult", "fetch_url", "result_url"):
        value = response.get(key)
        if isinstance(value, str) and media_utils.is_remote_url(value):
            return value
    data = response.get("data")
    if isinstance(data, dict):
        return _fetch_url(data)
    return None


def _request_id(response):
    """Extract a ModelsLab request ID.

    Args:
        response: Required. Provider response JSON.

    Returns:
        Request ID, or None.
    """
    if not isinstance(response, dict):
        return None
    for key in ("id", "request_id", "task_id", "track_id", "job_id"):
        if response.get(key):
            return response[key]
    data = response.get("data")
    if isinstance(data, dict):
        return _request_id(data)
    return None
