from ..._common import env_utils, http_utils
from ..post_processing import (
    build_result,
    decode_base64_audio,
    failure_result,
    save_audio_bytes,
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

PROVIDER = "google"
ENV_NAME = "GOOGLE_API_KEY"
DEFAULT_MODEL = None
COST_SOURCE = "unavailable"


def _selected_model(kwargs):
    """Return the requested Lyria model.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model.
    """
    return selected_model(kwargs, DEFAULT_MODEL, required=True)


def _build_payload(model, prepared, kwargs):
    """Build the Gemini generateContent payload.

    Args:
        model: Required. Lyria model name.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.
    """
    contents = kwargs.get("contents")
    if contents is None:
        contents = [{"parts": [{"text": prepared["prompt"]}]}]

    payload = {"contents": contents}
    add_if_present(payload, kwargs, "images", "response_format")
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload) | {"model"}))
    return payload


def _cost(model, kwargs):
    """Return unavailable Google Lyria cost metadata.

    Args:
        model: Required. Lyria model name.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate music with Google Lyria.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Local path for inline audio.
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
                "the full Gemini generateContent endpoint URL",
            )

        api_key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request_json(
            "POST",
            endpoint,
            headers={"x-goog-api-key": api_key},
            json=payload,
            timeout=request_timeout(kwargs),
            retries=request_retries(kwargs),
        )
        audio, mime_type = _extract_inline_audio(response)
        saved_path = save_audio_bytes(audio, output_path) if audio else None
        metadata = {"mime_type": mime_type} if mime_type else None
        return build_result(
            PROVIDER,
            model=model,
            status="completed" if audio else None,
            raw_response=response,
            output_path=saved_path,
            audio=None if saved_path else audio,
            cost=_cost(model, kwargs),
            provider_metadata=metadata,
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def _extract_inline_audio(response):
    """Extract inline audio from a Gemini response.

    Args:
        response: Required. Gemini response JSON.

    Returns:
        A tuple with audio bytes and MIME type.

    Raises:
        RuntimeError: If no inline audio is present.
    """
    for candidate in _walk(response):
        if not isinstance(candidate, dict):
            continue
        inline_data = candidate.get("inlineData") or candidate.get("inline_data")
        if not isinstance(inline_data, dict):
            continue
        data = inline_data.get("data")
        mime_type = inline_data.get("mimeType") or inline_data.get("mime_type")
        if data:
            return decode_base64_audio(data), mime_type
    raise RuntimeError("Google response did not include inline audio data.")


def _walk(value):
    """Yield nested values from dictionaries and lists.

    Args:
        value: Required. Value to walk.

    Yields:
        Nested values.
    """
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list | tuple):
        for item in value:
            yield from _walk(item)
