import base64

from ..._common import env_utils, provider_api

PROVIDER = "google"
ENV_NAME = "GOOGLE_API_KEY"
DEFAULT_MODEL = "lyria-3-pro-preview"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with Google Lyria.

    Args:
        lyrics: Required. Lyrics, sections, or song structure.
        prompt: Optional. Musical prompt, style, language, or duration notes.
        output_path: Optional. Local path for saving inline audio.
        sync: Optional. Ignored because this documented flow is synchronous.
        **kwargs: Optional. Google generation fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT.format(model=model))
    payload = _build_payload(lyrics, prompt=prompt, model=model, **kwargs)
    api_key = env_utils.require_env_var(ENV_NAME)
    response = provider_api.request_json(
        "POST",
        endpoint,
        params={"key": api_key},
        payload=payload,
        timeout=timeout,
    )
    return _result_from_inline_audio(response, model, output_path)


def _build_payload(lyrics, prompt=None, model=None, **kwargs):
    """Build a Google `generateContent` payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Musical prompt or style guide.
        model: Optional. Provider model name.
        **kwargs: Optional. Google generation fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    response_format = provider_api.pop_value(kwargs, "response_format", default=None)
    contents = provider_api.pop_value(kwargs, "contents", default=None)
    images = provider_api.pop_value(kwargs, "images", default=None)

    if contents is None:
        text = _compose_text(prompt, lyrics)
        parts = [{"text": text}]
        for image in images or ():
            if isinstance(image, dict):
                parts.append(image)
            else:
                parts.append({"inlineData": provider_api.media_as_inline_data(image)})
        contents = [{"role": "user", "parts": parts}]

    payload = {"contents": contents}
    if response_format is not None:
        payload["response_format"] = response_format
    return provider_api.merge_kwargs(payload, kwargs)


def _compose_text(prompt, lyrics):
    """Compose the textual instruction for Lyria.

    Args:
        prompt: Optional. Musical prompt or style guide.
        lyrics: Required. Lyrics or song structure.

    Returns:
        A prompt string.
    """
    pieces = []
    if prompt:
        pieces.append(str(prompt))
    pieces.append("Use these lyrics as the primary song structure:")
    pieces.append(str(lyrics))
    return "\n\n".join(pieces)


def _result_from_inline_audio(response, model, output_path=None):
    """Extract inline audio from a Google response.

    Args:
        response: Required. Parsed Google response.
        model: Required. Provider model name.
        output_path: Optional. Local destination path.

    Returns:
        A provider response dictionary.
    """
    for candidate in response.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                audio = base64.b64decode(inline["data"])
                saved_path = provider_api.save_bytes(audio, output_path)
                return {
                    "model": model,
                    "status": "completed",
                    "audio": None if saved_path else audio,
                    "output_path": saved_path,
                    "provider_metadata": {
                        "mime_type": inline.get("mimeType") or inline.get("mime_type"),
                    },
                    "raw_response": response,
                }

    response["model"] = model
    return response
