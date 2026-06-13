import requests

from .._common import (
    ApiRequestError,
    api_timeout,
    auth_header,
    complete_local_job_generation,
    format_response_error,
    reject_parameter_present,
    reject_unknown_kwargs,
    save_bytes,
    start_local_job,
    update_local_job_generation,
)

MODELS = {
    "music_v1": {
        "endpoint": "https://api.elevenlabs.io/v1/music",
        "status_endpoint": None,
        "result_endpoint": None,
        "doc": "https://elevenlabs.io/docs/api-reference/music/compose",
    },
}

ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"
ELEVENLABS_USD_PER_MINUTE = 0.150


def generate(lyrics, model="music_v1", **kwargs):
    """Submit one ElevenLabs Music job through a local background worker.

    ElevenLabs returns binary audio from the compose request. This wrapper starts
    that synchronous request in a local background thread and returns a local job
    dictionary immediately.

    Args:
        lyrics: Required. Song lyrics embedded in the provider prompt.
        model: Optional. Accepted values:
            - "music_v1": ElevenLabs Music v1 model.
        **kwargs: Optional provider parameters:
            - `prompt`: Required. Music prompt.
            - `negative_prompt`: Not supported by ElevenLabs Music compose.
              Passing a value raises `ValueError`.
            - `duration`: Song duration in seconds. Defaults to `60`.

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
    reject_unknown_kwargs(
        kwargs,
        {
            "duration",
            "_force_instrumental",
        },
    )

    extension = ELEVENLABS_OUTPUT_FORMAT.split("_", 1)[0]
    _validate_kwargs(kwargs)
    duration = kwargs.get("duration", 60)
    cost = _cost_for_duration(duration)

    def worker(output_path):
        payload = {"model_id": model}
        payload["music_length_ms"] = int(duration * 1000)
        payload["prompt"] = f"{prompt}\n\nUse these lyrics:\n{lyrics}"
        if "_force_instrumental" in kwargs:
            payload["force_instrumental"] = kwargs["_force_instrumental"]
        response = requests.post(
            MODELS[model]["endpoint"],
            headers=_headers(),
            params={"output_format": ELEVENLABS_OUTPUT_FORMAT},
            json=payload,
            timeout=api_timeout(240),
        )
        if response.status_code >= 400:
            raise ApiRequestError(format_response_error(response))
        save_bytes(response.content, output_path)
        return {
            "song_id": response.headers.get("X-Song-Id"),
            "content_type": response.headers.get("Content-Type"),
            "output_path": output_path,
        }

    return start_local_job(
        "elevenlabs",
        model,
        worker,
        extension,
        cost_usd=cost,
        cost_source="official_pricing_table",
        cost_is_estimated=True,
        cost_details={
            "duration_seconds": duration,
            "usd_per_minute": ELEVENLABS_USD_PER_MINUTE,
        },
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


def _validate_kwargs(kwargs):
    duration_ms = int(kwargs.get("duration", 60) * 1000)
    if not 3000 <= duration_ms <= 600000:
        raise ValueError("duration must be between 3 and 600 seconds")


def _cost_for_duration(duration):
    return round((duration / 60) * ELEVENLABS_USD_PER_MINUTE, 8)



