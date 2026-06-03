from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "topmediai"
ENV_NAME = "TOPMEDIAI_API_KEY"
DEFAULT_MODEL = "v4.5"
DEFAULT_BASE_URL = "https://api.topmediai.com"
DEFAULT_ENDPOINT = f"{DEFAULT_BASE_URL}/v3/music/generate"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit a TopMediai audio-reference music task."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    raw_response = http_utils.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        json=payload,
        timeout=timeout,
        retries=retries,
    )
    request_id = _request_id(raw_response)
    if not sync or not request_id:
        return build_result(
            PROVIDER,
            model,
            raw_response,
            output_path=output_path,
            status="submitted" if request_id else None,
            request_id=request_id,
            cost=_cost(model=model),
        )

    final_response = wait_for_result(
        lambda: get_generation_result(request_id, model=model, timeout=timeout, retries=retries),
        max_wait_seconds=kwargs.get("max_wait_seconds", 600),
        poll_interval=kwargs.get("poll_interval", 5),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch TopMediai task status."""
    base_url = kwargs.get("base_url", DEFAULT_BASE_URL)
    endpoint = kwargs.get("status_endpoint", f"{base_url}/v3/music/tasks")
    return http_utils.request_json(
        "GET",
        endpoint,
        headers=_headers(),
        params={"ids": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch TopMediai task result."""
    response = get_generation_status(request_id, model=model, **kwargs)
    return build_result(PROVIDER, model or DEFAULT_MODEL, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the TopMediai v3 music payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    payload.setdefault("action", kwargs.get("action", "generate"))
    if model is not None:
        payload.setdefault("mv", model)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "style"))
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "audio_url"),
        data_uri_field=kwargs.get("data_uri_field", "audio_data_uri"),
        file_id_field=kwargs.get("file_id_field", "file_id"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _cost(model=None, **kwargs):
    """Return TopMediai credit-based cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="topmediai_credits",
        details={"model": model, **kwargs},
    )


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"x-api-key": api_key}


def _request_id(response):
    if isinstance(response, dict):
        data = response.get("data")
        nested_id = data.get("id") if isinstance(data, dict) else None
        return (
            response.get("task_id")
            or response.get("taskId")
            or response.get("id")
            or nested_id
        )
    return None
