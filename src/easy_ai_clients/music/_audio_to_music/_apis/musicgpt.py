from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "musicgpt"
ENV_NAME = "MUSICGPT_API_KEY"
DEFAULT_MODEL = None
DEFAULT_ENDPOINT = "https://api.musicgpt.com/api/public/v1/MusicAI"
STATUS_ENDPOINT = "https://api.musicgpt.com/api/public/v1/byId"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit a MusicGPT audio-to-music task."""
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
    status_endpoint = kwargs.get("status_endpoint") or STATUS_ENDPOINT
    if not sync or not request_id:
        status = "submitted" if request_id else None
        return build_result(
            PROVIDER,
            model,
            raw_response,
            output_path=output_path,
            status=status,
            request_id=request_id,
            cost=_cost(model=model),
        )

    final_response = wait_for_result(
        lambda: get_generation_result(
            request_id,
            output_path=None,
            model=model,
            status_endpoint=status_endpoint,
            timeout=timeout,
            retries=retries,
        ),
        max_wait_seconds=kwargs.get("max_wait_seconds", 600),
        poll_interval=kwargs.get("poll_interval", 5),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch MusicGPT status."""
    endpoint = _format_status_endpoint(
        kwargs.get("status_endpoint") or STATUS_ENDPOINT,
        request_id,
    )
    return http_utils.request_json(
        "GET",
        endpoint,
        headers=_headers(),
        params=kwargs.get("params") or {
            "conversionType": "MUSIC_AI",
            "task_id": request_id,
        },
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch MusicGPT result from a caller-provided endpoint template."""
    response = get_generation_status(request_id, model=model, **kwargs)
    return build_result(PROVIDER, model, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the MusicGPT task payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    if model is not None:
        payload.setdefault("model", model)
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "audio_url"),
        data_uri_field=kwargs.get("data_uri_field", "audio"),
        file_id_field=kwargs.get("file_id_field", "file_id"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _cost(model=None, **kwargs):
    """Return unavailable MusicGPT cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="musicgpt_plan_billing",
        details={"model": model, **kwargs},
    )


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": api_key}


def _request_id(response):
    if isinstance(response, dict):
        return response.get("task_id") or response.get("taskId") or response.get("id")
    return None


def _format_status_endpoint(endpoint, request_id):
    if not endpoint:
        return None
    return endpoint.format(task_id=request_id, request_id=request_id, id=request_id)
