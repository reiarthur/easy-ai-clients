import requests

from .._common import (
    ApiRequestError,
    api_timeout,
    auth_header,
    complete_local_job_generation,
    format_response_error,
    normalize_duration,
    raise_input_limit_error,
    reject_parameter_present,
    reject_unknown_kwargs,
    save_bytes,
    start_local_job,
    text_limit_field,
    update_local_job_generation,
)

MODELS = {
    "music_v2": {
        "endpoint": "https://api.elevenlabs.io/v1/music",
        "status_endpoint": None,
        "result_endpoint": None,
        "doc": "https://elevenlabs.io/docs/api-reference/music/compose",
    },
}

ELEVENLABS_OUTPUT_FORMAT = "auto"
ELEVENLABS_OUTPUT_EXTENSION = "mp3"
ELEVENLABS_USD_PER_MINUTE = 0.150
ELEVENLABS_AUDIO_CONTENT_TYPES = {
    "application/octet-stream",
    "audio/aac",
    "audio/flac",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-m4a",
}


def generate(lyrics, model="music_v2", **kwargs):
    """Submit one ElevenLabs Music job through a local background worker.

    ElevenLabs returns binary audio from the compose request. This wrapper starts
    that synchronous request in a local background thread and returns a local job
    dictionary immediately.

    Args:
        lyrics: Required. Song lyrics embedded in the provider prompt.
        model: Optional. Accepted values:
            - "music_v2": ElevenLabs Music v2 model.
        **kwargs: Optional provider parameters:
            - `prompt`: Required. Music prompt.
            - `negative_prompt`: Not supported by ElevenLabs Music compose.
              Passing a value raises `ValueError`.
            - `duration`: Optional song duration in seconds. Valid numeric
              values are clamped to `3..600` and sent as `music_length_ms`.
              Missing or invalid values omit `music_length_ms`.

    Returns:
        A normalized generation dictionary.

    Raises:
        ValueError: If the model is unsupported, `prompt` is missing,
            `negative_prompt` is passed, or kwargs include unsupported keys.
    """
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")
    prompt = kwargs.pop("prompt", None)
    reject_parameter_present(kwargs, "negative_prompt", "elevenlabs")
    if prompt is None:
        raise ValueError("prompt is required for elevenlabs")
    duration = normalize_duration(kwargs.pop("duration", None), 3, 600, default=None)
    reject_unknown_kwargs(kwargs, set())

    cost = _cost_for_duration(duration)
    final_prompt = _prompt_with_lyrics(prompt, lyrics)
    _check_input_limits(model, final_prompt)

    def worker(output_path):
        payload = {"model_id": model}
        if duration is not None:
            payload["music_length_ms"] = int(duration * 1000)
        payload["prompt"] = final_prompt
        response = requests.post(
            MODELS[model]["endpoint"],
            headers=_headers(),
            params={"output_format": ELEVENLABS_OUTPUT_FORMAT},
            json=payload,
            timeout=api_timeout(240),
        )
        if response.status_code >= 400:
            raise ApiRequestError(format_response_error(response))
        save_bytes(_audio_content(response), output_path)
        return {
            "song_id": response.headers.get("X-Song-Id"),
            "content_type": response.headers.get("Content-Type"),
            "output_path": output_path,
        }

    return start_local_job(
        "elevenlabs",
        model,
        worker,
        ELEVENLABS_OUTPUT_EXTENSION,
        cost_usd=cost,
        cost_source="official_pricing_table" if cost is not None else None,
        cost_is_estimated=cost is not None,
        cost_details=_cost_details(duration),
    )


def get_status(generation):
    """Return an updated ElevenLabs generation dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        LocalJobError: If the local worker failed.
    """
    return update_local_job_generation(generation)


def download_result(generation):
    """Return the completed ElevenLabs generation dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        LocalJobError: If the local worker failed.
    """
    return complete_local_job_generation(generation)


def _headers():
    headers = auth_header("ELEVENLABS_API_KEY", "xi-api-key")
    headers["Content-Type"] = "application/json"
    return headers


def _prompt_with_lyrics(prompt, lyrics):
    return "\n".join(
        [
            prompt,
            "",
            "Lyrics language and delivery:",
            "- Use the language indicated by the lyrics and music guidance.",
            "- Sing with natural native diction and preserve complete word endings.",
            "- Respect accents, diacritics, and language-specific pronunciation.",
            "- Use section tags only as structure, not as sung words.",
            "- Keep a natural pace with short musical breathing room between sections.",
            *_language_specific_rules(prompt, lyrics),
            "",
            "Avoid robotic vocals, forced belting, swallowed word endings, rushed syllables,",
            "thin instruments, low backing track, foreign accent, chaotic sound design,",
            "dissonance, hiss, and overcompressed karaoke backing.",
            "",
            "Lyrics:",
            lyrics,
        ]
    )


def _language_specific_rules(prompt, lyrics):
    text = f"{prompt}\n{lyrics}".lower()
    if any(marker in text for marker in ("brazilian portuguese", "português", "portugues", "pt-br")):
        return [
            "- For Brazilian Portuguese, keep cedilla and nasal vowel sounds natural and clear.",
        ]
    return []


def _check_input_limits(model, prompt):
    limit = text_limit_field(prompt, 4100)
    if limit is not None:
        raise_input_limit_error("elevenlabs", model, {"prompt": limit})


def _cost_for_duration(duration):
    if duration is None:
        return None
    return round((duration / 60) * ELEVENLABS_USD_PER_MINUTE, 8)


def _cost_details(duration):
    if duration is None:
        return {}
    return {
        "duration_seconds": duration,
        "usd_per_minute": ELEVENLABS_USD_PER_MINUTE,
    }


def _audio_content(response):
    content = response.content or b""
    if not content:
        raise RuntimeError("ElevenLabs music response did not include audio data")
    content_type = _content_type(response)
    if not _is_audio_content_type(content_type):
        detail = format_response_error(response)
        raise RuntimeError(f"ElevenLabs music response was not audio content: {detail}")
    return content


def _content_type(response):
    return str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()


def _is_audio_content_type(content_type):
    return content_type.startswith("audio/") or content_type in ELEVENLABS_AUDIO_CONTENT_TYPES



