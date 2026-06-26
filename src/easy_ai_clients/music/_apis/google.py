import base64
import binascii
import json

from .._common import (
    api_timeout,
    auth_header,
    complete_local_job_generation,
    duration_phrase,
    normalize_duration,
    raise_input_limit_error,
    reject_parameter_present,
    reject_unknown_kwargs,
    request_json,
    sanitize,
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
GOOGLE_INPUT_TOKEN_LIMIT = 131072
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
            - `duration`: Ignored for Clip. For Pro, valid numeric values are
              clamped to `15..180` and added to the prompt as natural English.

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
    duration = _duration_for_model(model, kwargs.pop("duration", None))
    reject_unknown_kwargs(kwargs, set())

    final_prompt = _prompt_with_duration(model, prompt, duration)
    payload = _payload(final_prompt, lyrics)
    _check_token_limit(model, payload)

    def worker(output_path):
        response = request_json(
            "POST",
            MODELS[model]["endpoint"],
            headers=_headers(),
            json_payload=payload,
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


def _duration_for_model(model, value):
    if model == "lyria-3-pro-preview":
        return normalize_duration(value, 15, 180, default=None)
    return None


def _prompt_with_duration(model, prompt, duration):
    if model != "lyria-3-pro-preview" or duration is None:
        return prompt
    phrase = f"Target song duration: {duration_phrase(duration)}."
    if "target song duration:" in prompt.lower():
        return prompt
    return f"{prompt}\n\n{phrase}"


def _payload(prompt, lyrics):
    return {
        "contents": [{"parts": [{"text": f"{prompt}\n\nLyrics:\n{lyrics}"}]}],
    }


def _check_token_limit(model, payload):
    response = request_json(
        "POST",
        MODELS[model]["endpoint"].replace(":generateContent", ":countTokens"),
        headers=_headers(),
        json_payload=payload,
        timeout=api_timeout(60),
    )
    total_tokens = _total_tokens(response)
    if total_tokens is None:
        raise RuntimeError("Google countTokens response did not include totalTokens")
    if total_tokens > GOOGLE_INPUT_TOKEN_LIMIT:
        raise_input_limit_error(
            "google",
            model,
            {
                "contents": {
                    "unit": "tokens",
                    "maximum": GOOGLE_INPUT_TOKEN_LIMIT,
                    "observed": total_tokens,
                }
            },
        )


def _total_tokens(response):
    if not isinstance(response, dict):
        return None
    for key in ("totalTokens", "total_tokens"):
        value = response.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def _inline_audio(response):
    if not isinstance(response, dict):
        raise RuntimeError("Google Lyria response was not a JSON object")

    candidates = response.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError(_no_audio_message(response))

    candidate_details = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            candidate_details.append({"index": index, "reason": "candidate was not an object"})
            continue

        candidate_details.append(_candidate_details(index, candidate))
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue

        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline, dict) and inline.get("data"):
                try:
                    return base64.b64decode(inline["data"], validate=True)
                except (binascii.Error, TypeError, ValueError):
                    raise RuntimeError(
                        "Google Lyria response included invalid inline audio data"
                    ) from None

    raise RuntimeError(_no_audio_message(response, candidate_details))


def _no_audio_message(response, candidate_details=None):
    details = {}
    prompt_feedback = response.get("promptFeedback") if isinstance(response, dict) else None
    if prompt_feedback:
        details["promptFeedback"] = prompt_feedback
    if candidate_details:
        details["candidates"] = candidate_details
    if not details:
        return "Google Lyria response did not include usable inline audio data"
    safe = json.dumps(sanitize(details), ensure_ascii=False)[:1200]
    return f"Google Lyria response did not include usable inline audio data: {safe}"


def _candidate_details(index, candidate):
    details = {"index": index}
    for key in ("finishReason", "finishMessage", "safetyRatings"):
        if key in candidate:
            details[key] = candidate.get(key)

    content = candidate.get("content")
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            details["partTypes"] = _part_types(parts)
        else:
            details["reason"] = "content.parts was not a list"
    else:
        details["reason"] = "content was not an object"
    return details


def _part_types(parts):
    types = []
    for part in parts:
        if not isinstance(part, dict):
            types.append("non_object")
        elif part.get("inlineData") or part.get("inline_data"):
            types.append("inline_audio")
        elif "text" in part:
            types.append("text")
        else:
            types.append("unknown")
    return types



