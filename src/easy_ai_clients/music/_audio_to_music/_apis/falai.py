from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "falai"
ENV_NAME = "FAL_KEY"
DEFAULT_MODEL = "fal-ai/minimax-music/v2.6"
DEFAULT_QUEUE_BASE_URL = "https://queue.fal.run"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit an audio-to-music job to a fal.ai model queue."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    model_id = kwargs.pop("model_id", model)
    endpoint = kwargs.pop("endpoint", f"{DEFAULT_QUEUE_BASE_URL}/{model_id}")
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    raw_response = http_utils.request_json(
        "POST",
        endpoint,
        headers=_headers(kwargs),
        json=payload,
        timeout=timeout,
        retries=retries,
    )
    request_id = _request_id(raw_response)
    metadata = {"model_id": model_id}
    if not sync or not request_id:
        return build_result(
            PROVIDER,
            model,
            raw_response,
            output_path=output_path,
            status="submitted" if request_id else None,
            request_id=request_id,
            provider_metadata=metadata,
            cost=_cost(model=model),
        )

    final_response = wait_for_result(
        lambda: get_generation_result(
            request_id,
            model=model,
            model_id=model_id,
            timeout=timeout,
            retries=retries,
        ),
        max_wait_seconds=kwargs.get("max_wait_seconds", 600),
        poll_interval=kwargs.get("poll_interval", 5),
    )
    return build_result(
        PROVIDER,
        model,
        final_response,
        output_path=output_path,
        provider_metadata=metadata,
        cost=_cost(model=model),
    )


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch fal.ai queue status."""
    model_id = kwargs.get("model_id", model or DEFAULT_MODEL)
    endpoint = kwargs.get(
        "status_endpoint",
        f"{DEFAULT_QUEUE_BASE_URL}/{model_id}/requests/{request_id}/status",
    )
    return http_utils.request_json(
        "GET",
        endpoint,
        headers=_headers(kwargs),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch fal.ai queue result."""
    model_id = kwargs.get("model_id", model or DEFAULT_MODEL)
    endpoint = kwargs.get(
        "result_endpoint",
        f"{DEFAULT_QUEUE_BASE_URL}/{model_id}/requests/{request_id}/response",
    )
    response = http_utils.request_json(
        "GET",
        endpoint,
        headers=_headers(kwargs),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )
    return build_result(PROVIDER, model, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build a fal.ai model payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "reference_audio"),
        data_uri_field=kwargs.get("data_uri_field", "reference_audio"),
        file_id_field=kwargs.get("file_id_field"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _cost(model=None, **kwargs):
    """Return unavailable fal.ai model-specific cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="falai_model_pricing",
        details={"model": model, **kwargs},
    )


def _headers(kwargs=None):
    api_key = env_utils.require_env_var(ENV_NAME)
    headers = {"Authorization": f"Key {api_key}"}
    kwargs = kwargs or {}
    if kwargs.get("fal_request_timeout") is not None:
        headers["X-Fal-Request-Timeout"] = str(kwargs["fal_request_timeout"])
    if kwargs.get("fal_no_retry") is not None:
        headers["X-Fal-No-Retry"] = str(kwargs["fal_no_retry"]).lower()
    return headers


def _request_id(response):
    if isinstance(response, dict):
        return response.get("request_id") or response.get("requestId")
    return None
