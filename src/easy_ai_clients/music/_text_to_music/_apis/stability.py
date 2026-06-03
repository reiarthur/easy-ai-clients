from ..._common import env_utils, http_utils
from ..post_processing import build_result, failure_result, save_audio_bytes, unavailable_cost
from ..pre_processing import (
    add_if_present,
    missing_endpoint_error,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "stability"
ENV_NAME = "STABILITY_API_KEY"
DEFAULT_MODEL = None
COST_SOURCE = "unavailable"


def _selected_model(kwargs):
    """Return the requested Stable Audio model.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model, if provided.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the Stable Audio text generation payload.

    Args:
        model: Optional. Stable Audio model.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.
    """
    payload = {"prompt": prepared["prompt"]}
    if model:
        payload["model"] = model
    add_if_present(payload, kwargs, "duration", "format", "negative_prompt")
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable Stability cost metadata.

    Args:
        model: Optional. Stable Audio model.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate instrumental music with Stability Stable Audio.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path for binary audio.
        sync: Optional. Present for operation consistency.
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
                "the Stable Audio text generation endpoint URL",
            )

        api_key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request(
            "POST",
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )
        content_type = response.headers.get("content-type")
        if content_type and "application/json" in content_type:
            raw_response = http_utils.response_json(response)
            return build_result(
                PROVIDER,
                model=model,
                raw_response=raw_response,
                cost=_cost(model, kwargs),
            )

        audio = response.content
        saved_path = save_audio_bytes(audio, output_path) if output_path else None
        raw_response = {
            "content_type": content_type,
            "content_length": len(audio),
            "status_code": response.status_code,
        }
        return build_result(
            PROVIDER,
            model=model,
            status="completed",
            raw_response=raw_response,
            output_path=saved_path,
            audio=None if saved_path else audio,
            cost=_cost(model, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)
