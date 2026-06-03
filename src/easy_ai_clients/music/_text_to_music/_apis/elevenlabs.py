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

PROVIDER = "elevenlabs"
ENV_NAME = "ELEVENLABS_API_KEY"
DEFAULT_MODEL = "music_v1"
COST_SOURCE = "unavailable"


def _selected_model(kwargs):
    """Return the ElevenLabs music model.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the ElevenLabs music composition payload.

    Args:
        model: Required. Music model.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.

    Raises:
        ValueError: If prompt and composition_plan are both sent.
    """
    composition_plan = kwargs.get("composition_plan")
    if composition_plan is not None:
        if "prompt" in kwargs:
            raise ValueError("Send either prompt or composition_plan, not both.")
        payload = {"composition_plan": composition_plan}
    else:
        payload = {"prompt": prepared["prompt"]}

    if model:
        payload["model"] = model
    add_if_present(
        payload,
        kwargs,
        "music_length_ms",
        "output_format",
        "respect_sections_durations",
    )
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable ElevenLabs cost metadata.

    Args:
        model: Required. Music model.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate music with ElevenLabs Music API.

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
                "the full music composition endpoint URL",
            )

        api_key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request(
            "POST",
            endpoint,
            headers={"xi-api-key": api_key},
            json=payload,
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )
        content_type = response.headers.get("content-type")
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
