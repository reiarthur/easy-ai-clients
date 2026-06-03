from copy import deepcopy

from ..._common import provider_api

PROVIDER = "elevenlabs"
ENV_NAME = "ELEVENLABS_API_KEY"
DEFAULT_MODEL = "music_v1"
ENDPOINT = "https://api.elevenlabs.io/v1/music/compose"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with ElevenLabs Music.

    Args:
        lyrics: Required. Lyrics, sections, or song structure.
        prompt: Optional. Musical direction. Not sent with `composition_plan`.
        output_path: Optional. Local path for saving returned audio.
        sync: Optional. Ignored because composition returns audio directly.
        **kwargs: Optional. ElevenLabs composition fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    payload = _build_payload(lyrics, prompt=prompt, model=model, **kwargs)
    headers = provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="xi-api-key",
        extra={"Content-Type": "application/json"},
    )
    audio = provider_api.request_binary(
        "POST",
        endpoint,
        headers=headers,
        payload=payload,
        timeout=timeout,
    )
    saved_path = provider_api.save_bytes(audio, output_path)
    return {
        "model": model,
        "status": "completed",
        "audio": None if saved_path else audio,
        "output_path": saved_path,
        "provider_metadata": {
            "output_format": payload.get("output_format"),
            "music_length_ms": payload.get("music_length_ms"),
        },
    }


def _build_payload(lyrics, prompt=None, model=None, **kwargs):
    """Build an ElevenLabs composition payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Musical direction.
        model: Optional. Provider model name.
        **kwargs: Optional. ElevenLabs composition fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    composition_plan = provider_api.pop_value(kwargs, "composition_plan", default=None)
    if composition_plan is not None and prompt is not None:
        raise ValueError("ElevenLabs accepts either prompt or composition_plan, not both.")

    if composition_plan is None:
        section_name = provider_api.pop_value(kwargs, "section_name", default="song")
        section = {"section_name": section_name, "lyrics": lyrics}
        if prompt is not None:
            section["description"] = prompt
        composition_plan = {"sections": [section]}
    else:
        composition_plan = deepcopy(composition_plan)
        _attach_lyrics_to_plan(composition_plan, lyrics)

    payload = {"composition_plan": composition_plan}
    if model is not None:
        payload["model_id"] = model
    return provider_api.merge_kwargs(payload, kwargs)


def _attach_lyrics_to_plan(composition_plan, lyrics):
    """Attach lyrics to a composition plan when it has no lyrics field.

    Args:
        composition_plan: Required. Mutable composition plan.
        lyrics: Required. Lyrics or song structure.

    Returns:
        None.
    """
    sections = composition_plan.get("sections")
    if isinstance(sections, list) and sections:
        first = sections[0]
        if isinstance(first, dict) and "lyrics" not in first:
            first["lyrics"] = lyrics
        return
    if "lyrics" not in composition_plan:
        composition_plan["lyrics"] = lyrics
