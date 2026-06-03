from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "replicate"
ENV_NAME = "REPLICATE_API_TOKEN"
DEFAULT_MODEL = "minimax/music-2.6"
DEFAULT_ENDPOINT = "https://api.replicate.com/v1/predictions"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Create a Replicate prediction for a hosted music model."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    raw_response = http_utils.request_json(
        "POST",
        endpoint,
        headers=_headers(wait=sync),
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
        completed_statuses=("succeeded",),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch a Replicate prediction."""
    return http_utils.request_json(
        "GET",
        f"{DEFAULT_ENDPOINT}/{request_id}",
        headers=_headers(),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch a Replicate prediction result."""
    response = get_generation_status(request_id, model=model, **kwargs)
    return build_result(PROVIDER, model or DEFAULT_MODEL, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the Replicate Predictions API payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = {}
    version = kwargs.get("version")
    if version:
        payload["version"] = version
    else:
        payload["model"] = model or DEFAULT_MODEL
    input_payload = dict(kwargs.get("input") or {})
    input_payload.update(without_internal_kwargs(kwargs))
    input_payload.pop("version", None)
    input_payload.pop("input", None)
    input_payload.pop("webhook", None)
    add_prompt(input_payload, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    apply_audio_reference(
        input_payload,
        audio,
        url_field=kwargs.get("url_field", "input_audio"),
        data_uri_field=kwargs.get("data_uri_field", "input_audio"),
        file_id_field=kwargs.get("file_id_field"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    payload["input"] = input_payload
    if kwargs.get("webhook"):
        payload["webhook"] = kwargs["webhook"]
    return payload


def _cost(model=None, **kwargs):
    """Return Replicate cost metadata when present in provider data."""
    response_cost = cost_utils.cost_from_response(kwargs)
    if cost_utils.has_available_cost(response_cost):
        return response_cost
    return cost_utils.unavailable_cost_metadata(
        details={"model": model, **kwargs},
    )


def update_cost(result, **kwargs):
    """Refresh Replicate cost metadata from documented output pricing.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    model = result.get("model") if isinstance(result, dict) else None
    cost = _cost(model or DEFAULT_MODEL)
    return cost_utils.apply_cost_metadata(result, cost)


def _headers(wait=False):
    api_key = env_utils.require_env_var(ENV_NAME)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if wait:
        headers["Prefer"] = "wait"
    return headers


def _request_id(response):
    if isinstance(response, dict):
        return response.get("id")
    return None
