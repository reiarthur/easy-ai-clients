from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    audio_to_multipart_file,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "deapi"
ENV_NAME = "DEAPI_API_KEY"
DEFAULT_MODEL = "ACE-Step-v1.5-turbo"
DEFAULT_ENDPOINT = "https://api.deapi.ai/api/v2/audio/music"
DEFAULT_STATUS_ENDPOINT = "https://api.deapi.ai/api/v2/jobs/{request_id}"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit a deAPI txt2music request with reference audio."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    data, files = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    response = http_utils.multipart_request(
        "POST",
        endpoint,
        headers=_headers(),
        data=data,
        files=files,
        timeout=timeout,
        retries=retries,
    )
    raw_response = http_utils.response_json(response)
    raw_response.setdefault("cost_details", _cost_details(model, data))
    request_id = _request_id(raw_response)
    result_endpoint = kwargs.get("result_endpoint") or kwargs.get("status_endpoint") or DEFAULT_STATUS_ENDPOINT
    if not sync or not request_id:
        warnings = None
        return build_result(
            PROVIDER,
            model,
            raw_response,
            output_path=output_path,
            status="submitted" if request_id else None,
            request_id=request_id,
            warnings=warnings,
            cost=_cost(model=model, payload=data),
        )

    final_response = wait_for_result(
        lambda: get_generation_result(
            request_id,
            model=model,
            result_endpoint=result_endpoint,
            timeout=timeout,
            retries=retries,
        ),
        max_wait_seconds=kwargs.get("max_wait_seconds", 600),
        poll_interval=kwargs.get("poll_interval", 5),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch deAPI status."""
    endpoint = _format_endpoint(
        kwargs.get("result_endpoint") or kwargs.get("status_endpoint") or DEFAULT_STATUS_ENDPOINT,
        request_id,
    )
    if not endpoint:
        raise RuntimeError("A deAPI status endpoint is required for polling.")
    response = http_utils.request_json(
        "GET",
        endpoint,
        headers=_headers(),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )
    response.setdefault("request_id", request_id)
    response.setdefault("cost_details", _cost_details(model, kwargs))
    return response


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch deAPI result using a caller-provided endpoint template."""
    response = get_generation_status(request_id, model=model, **kwargs)
    return build_result(PROVIDER, model, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the deAPI multipart txt2music payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    data = without_internal_kwargs(kwargs)
    add_prompt(data, prompt, field_name=kwargs.get("prompt_field", "caption"))
    if model is not None:
        data.setdefault("model", model)
    data.setdefault("lyrics", kwargs.get("lyrics", "[Instrumental]"))
    files = audio_to_multipart_file(
        audio,
        field_name=kwargs.get("file_field", "reference_audio"),
        filename=kwargs.get("filename"),
        mime_type=kwargs.get("mime_type"),
        timeout=kwargs.get("timeout", 60),
    )
    return data, files


def _cost(model=None, payload=None, **kwargs):
    """Return unavailable deAPI cost metadata."""
    details = {"model": model, **kwargs}
    if payload:
        details.update({
            "duration": payload.get("duration"),
            "inference_steps": payload.get("inference_steps"),
        })
    return cost_utils.unavailable_cost_metadata(
        details=details,
    )


def update_cost(result, **kwargs):
    """Refresh deAPI cost metadata with the documented price endpoint.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    details = _cost_lookup_details(result)
    payload = {
        "model": details.get("model") or DEFAULT_MODEL,
        "duration": details.get("duration") or 30,
        "inference_steps": details.get("inference_steps") or 8,
    }
    try:
        response = http_utils.request_json(
            "POST",
            _price_endpoint(kwargs),
            headers=_headers(),
            json=payload,
            timeout=kwargs.get("timeout", 60),
            retries=kwargs.get("retries", 2),
        )
        cost = cost_utils.normalize_cost(
            _price_from_response(response),
            source="provider_response",
            is_estimated=True,
            details={
                "price_endpoint": "/api/v2/audio/music/price",
                **payload,
            },
        )
    except Exception:
        cost = cost_utils.unavailable_cost_metadata()
    return cost_utils.apply_cost_metadata(result, cost)


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}


def _request_id(response):
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict):
            return data.get("request_id") or data.get("requestId") or data.get("id")
        return response.get("request_id") or response.get("requestId") or response.get("id")
    return None


def _cost_details(model, payload):
    """Return deAPI cost lookup details.

    Args:
        model: Optional. deAPI model.
        payload: Required. Request payload.

    Returns:
        Cost detail fields.
    """
    return {
        "model": model or (payload or {}).get("model") or DEFAULT_MODEL,
        "duration": (payload or {}).get("duration"),
        "inference_steps": (payload or {}).get("inference_steps"),
    }


def _cost_lookup_details(result):
    """Return deAPI price calculation fields from a result.

    Args:
        result: Required. Normalized result dictionary.

    Returns:
        Cost lookup details.
    """
    details = {}
    if isinstance(result, dict):
        details.update(result.get("cost_details") or {})
        if result.get("model") is not None:
            details.setdefault("model", result["model"])
    return details


def _price_endpoint(kwargs):
    """Return the deAPI price calculation endpoint.

    Args:
        kwargs: Required. Provider options.

    Returns:
        Endpoint URL.
    """
    endpoint = kwargs.get("price_endpoint")
    if endpoint:
        return endpoint
    base_url = kwargs.get("base_url", "https://api.deapi.ai").rstrip("/")
    return f"{base_url}/api/v2/audio/music/price"


def _price_from_response(response):
    """Extract deAPI price from a price calculation response.

    Args:
        response: Required. Provider response.

    Returns:
        The price value.
    """
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict) and data.get("price") is not None:
            return data["price"]
        if response.get("price") is not None:
            return response["price"]
    raise RuntimeError("deAPI price calculation response did not include data.price.")


def _format_endpoint(endpoint, request_id):
    if not endpoint:
        return None
    return endpoint.format(request_id=request_id, id=request_id)
