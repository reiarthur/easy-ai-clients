import base64

from ..._common import env_utils, media_utils, provider_api

PROVIDER = "google"
ENV_NAME = "GOOGLE_API_KEY"
DEFAULT_MODEL = "lyria-3-pro-preview"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate_media_to_music(media, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate music from visual media with Google Lyria.

    Args:
        media: Required. Image or visual media guidance.
        prompt: Optional. Musical prompt.
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
    payload, metadata = _build_payload(media, prompt=prompt, model=model, **kwargs)
    api_key = env_utils.require_env_var(ENV_NAME)
    response = provider_api.request_json(
        "POST",
        endpoint,
        params={"key": api_key},
        payload=payload,
        timeout=timeout,
    )
    return _result_from_inline_audio(response, model, output_path, metadata)


def _build_payload(media, prompt=None, model=None, **kwargs):
    """Build a Google media-guided generation payload.

    Args:
        media: Required. Media input or list of media inputs.
        prompt: Optional. Musical prompt.
        model: Optional. Provider model name.
        **kwargs: Optional. Google fields.

    Returns:
        A `(payload, metadata)` tuple.
    """
    contents = provider_api.pop_value(kwargs, "contents", default=None)
    media_values = media if isinstance(media, list | tuple) else [media]
    metadata = [provider_api.safe_media_metadata(item) for item in media_values]

    if contents is None:
        parts = [{"text": prompt or "Create music guided by the supplied visual media."}]
        parts.extend(_media_part(item) for item in media_values)
        contents = [{"role": "user", "parts": parts}]

    payload = {"contents": contents}
    return provider_api.merge_kwargs(payload, kwargs), {"input_media": metadata}


def _media_part(media):
    """Build a Google media part.

    Args:
        media: Required. Media input.

    Returns:
        A Google content part dictionary.
    """
    if media_utils.is_remote_url(media):
        return {
            "fileData": {
                "fileUri": media,
                "mimeType": media_utils.infer_mime_type(media),
            }
        }
    return {"inlineData": provider_api.media_as_inline_data(media)}


def _result_from_inline_audio(response, model, output_path=None, metadata=None):
    """Extract inline audio from a Google response.

    Args:
        response: Required. Parsed Google response.
        model: Required. Provider model name.
        output_path: Optional. Local destination path.
        metadata: Optional. Safe provider metadata.

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
                provider_metadata = dict(metadata or {})
                provider_metadata["mime_type"] = inline.get("mimeType") or inline.get("mime_type")
                return {
                    "model": model,
                    "status": "completed",
                    "audio": None if saved_path else audio,
                    "output_path": saved_path,
                    "provider_metadata": provider_metadata,
                    "raw_response": response,
                }

    response["model"] = model
    response["provider_metadata"] = metadata
    return response
