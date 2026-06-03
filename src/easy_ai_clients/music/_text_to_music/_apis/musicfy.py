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
    missing_endpoint_error,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "musicfy"
ENV_NAME = "MUSICFY_API_KEY"
DEFAULT_MODEL = None
COST_SOURCE = "unavailable"


def _selected_model(kwargs):
    """Return the selected Musicfy model.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model, if provided.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the Musicfy text-to-music payload.

    Args:
        model: Optional. Musicfy model or mode.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.
    """
    payload = {"prompt": prepared["prompt"]}
    if model:
        payload["model"] = model
    add_if_present(payload, kwargs, "voice_id", "style", "duration", "format")
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable Musicfy cost metadata.

    Args:
        model: Optional. Musicfy model or mode.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate music with Musicfy.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path when a final URL is returned.
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
                "the Musicfy text-to-music endpoint URL and exact payload contract",
            )

        api_key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request_json(
            "POST",
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )
        audio_url = first_audio_url(response)
        saved_path = download_audio(
            audio_url,
            output_path,
            timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
        )
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            audio_url=audio_url,
            output_path=saved_path,
            cost=_cost(model, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)
