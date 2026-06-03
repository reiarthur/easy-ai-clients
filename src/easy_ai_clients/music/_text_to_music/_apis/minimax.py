from ..._common import env_utils, http_utils
from ..post_processing import (
    build_result,
    download_audio,
    failure_result,
    first_audio_url,
    save_audio_bytes,
    unavailable_cost,
)
from ..pre_processing import (
    add_if_present,
    endpoint_from_base,
    missing_endpoint_error,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "minimax"
ENV_NAME = "MINIMAX_API_KEY"
DEFAULT_MODEL = "music-2.6"
COST_SOURCE = "unavailable"
GENERATE_PATH = "/v1/music_generation"


def _selected_model(kwargs):
    """Return the selected MiniMax music model.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model.
    """
    return selected_model(kwargs, DEFAULT_MODEL, required=True)


def _build_payload(model, prepared, kwargs):
    """Build the MiniMax music_generation payload.

    Args:
        model: Required. MiniMax model.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.
    """
    payload = {
        "model": model,
        "prompt": prepared["prompt"],
    }
    add_if_present(
        payload,
        kwargs,
        "lyrics",
        "is_instrumental",
        "lyrics_optimizer",
        "stream",
        "output_format",
        "audio_setting",
        "audio_url",
        "audio_base64",
        "refer_voice_id",
    )
    if "output_format" not in payload:
        payload["output_format"] = "url"
    if (
        "lyrics" not in payload
        and "is_instrumental" not in payload
        and not payload.get("lyrics_optimizer")
    ):
        payload["is_instrumental"] = True
    payload.update(safe_payload_kwargs(kwargs, handled=set(payload)))
    return payload


def _cost(model, kwargs):
    """Return unavailable MiniMax cost metadata.

    Args:
        model: Required. MiniMax model.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    return unavailable_cost(COST_SOURCE)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate music with MiniMax Music API.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path when final audio is available.
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

        endpoint = kwargs.get("endpoint_url") or endpoint_from_base(
            kwargs.get("base_url"),
            GENERATE_PATH,
        )
        if not endpoint:
            raise missing_endpoint_error(PROVIDER, "the MiniMax API base URL")

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
        audio = None
        saved_path = None
        if audio_url:
            saved_path = download_audio(
                audio_url,
                output_path,
                timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
            )
        else:
            audio_hex = _extract_hex_audio(response)
            if audio_hex:
                audio = bytes.fromhex(audio_hex)
                saved_path = save_audio_bytes(audio, output_path) if output_path else None

        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            audio_url=audio_url,
            output_path=saved_path,
            audio=None if saved_path else audio,
            cost=_cost(model, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def _extract_hex_audio(response):
    """Extract hex-encoded audio from a MiniMax response.

    Args:
        response: Required. Provider response JSON.

    Returns:
        Hex audio string, or None.
    """
    for candidate in _walk(response):
        if not isinstance(candidate, dict):
            continue
        for key in ("hex", "audio_hex", "audioHex"):
            value = candidate.get(key)
            if isinstance(value, str) and value:
                return value
    return None


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
