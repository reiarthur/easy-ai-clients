import base64

from .._common import (
    api_timeout,
    auth_header,
    complete_local_job_generation,
    reject_parameter_present,
    reject_unknown_kwargs,
    request_json,
    save_bytes,
    start_local_job,
    update_local_job_generation,
)

MODELS = {
    "lyria-3-clip-preview": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/lyria-3-clip-preview:generateContent",
        "status_endpoint": None,
        "result_endpoint": None,
        "doc": "https://ai.google.dev/gemini-api/docs/music-generation",
    },
    "lyria-3-pro-preview": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/lyria-3-pro-preview:generateContent",
        "status_endpoint": None,
        "result_endpoint": None,
        "doc": "https://ai.google.dev/gemini-api/docs/music-generation",
    },
}

GOOGLE_OUTPUT_FORMAT = "mp3"
GOOGLE_MODEL_COSTS = {
    "lyria-3-clip-preview": 0.04,
    "lyria-3-pro-preview": 0.08,
}


def generate(lyrics, model="lyria-3-clip-preview", **kwargs):
    """Submit one Google Lyria job through a local background worker.

    Google Lyria returns inline audio in the generation response. This wrapper
    starts that synchronous request in a local background thread and returns a
    local job dictionary immediately.

    Args:
        lyrics: Required. Song lyrics embedded in the text prompt.
        model: Optional. Accepted values:
            - "lyria-3-clip-preview": Cheapest validated default.
            - "lyria-3-pro-preview": Higher-cost preview model.
        **kwargs: Optional provider parameters:
            - `prompt`: Required. Music prompt.
            - `negative_prompt`: Not supported by Google Lyria.
              Passing a value raises `ValueError`.
            - `duration`: Accepted for public standardization but ignored.

    Returns:
        A normalized generation dictionary.

    Raises:
        ValueError: If the model is unsupported, `prompt` is missing,
            `negative_prompt` is passed, or kwargs include unsupported keys.
    """
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")
    prompt = kwargs.pop("prompt", None)
    reject_parameter_present(kwargs, "negative_prompt", "google")
    if prompt is None:
        raise ValueError("prompt is required for google")
    reject_unknown_kwargs(kwargs, {"duration"})

    def worker(output_path):
        response = request_json(
            "POST",
            MODELS[model]["endpoint"],
            headers=_headers(),
            json_payload=_payload(prompt, lyrics),
            timeout=api_timeout(240),
        )
        save_bytes(_inline_audio(response), output_path)
        return response

    return start_local_job(
        "google",
        model,
        worker,
        GOOGLE_OUTPUT_FORMAT,
        cost_usd=GOOGLE_MODEL_COSTS.get(model),
        cost_source="official_pricing_table",
        cost_is_estimated=True,
        cost_details={"pricing_unit": "request"},
    )


def get_status(generation):
    """Return an updated Google Lyria generation dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        LocalJobError: If the local worker failed.
    """
    return update_local_job_generation(generation)


def download_result(generation):
    """Return the completed Google Lyria generation dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        LocalJobError: If the local worker failed.
    """
    return complete_local_job_generation(generation)


def _headers():
    headers = auth_header("GOOGLE_API_KEY", "x-goog-api-key")
    headers["Content-Type"] = "application/json"
    return headers


def _payload(prompt, lyrics):
    return {
        "contents": [{"parts": [{"text": f"{prompt}\n\nLyrics:\n{lyrics}"}]}],
    }


def _inline_audio(response):
    for candidate in response["candidates"]:
        for part in candidate["content"]["parts"]:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise RuntimeError("Google Lyria response did not include inline audio data")



