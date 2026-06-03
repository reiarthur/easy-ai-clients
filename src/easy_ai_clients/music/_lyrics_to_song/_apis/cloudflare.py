from ..._common import env_utils, provider_api

PROVIDER = "cloudflare"
ENV_NAME = "CLOUDFLARE_API_TOKEN"
ACCOUNT_ENV_NAME = "CLOUDFLARE_ACCOUNT_ID"
DEFAULT_MODEL = "minimax/music-2.6"
ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with Cloudflare Workers AI.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        output_path: Optional. Local destination for returned audio URL.
        sync: Optional. Ignored because this flow is single-call REST.
        **kwargs: Optional. Workers AI fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    account_id = provider_api.pop_value(kwargs, "account_id", default=None)
    if account_id is None:
        account_id = env_utils.require_env_var(ACCOUNT_ENV_NAME)
    endpoint = provider_api.pop_value(
        kwargs,
        "endpoint",
        default=ENDPOINT.format(account_id=account_id),
    )
    payload = _build_payload(lyrics, prompt=prompt, model=model, **kwargs)
    headers = provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Content-Type": "application/json"},
    )
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=headers,
        payload=payload,
        timeout=timeout,
    )
    response["model"] = model
    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


def _build_payload(lyrics, prompt=None, model=None, **kwargs):
    """Build a Cloudflare MiniMax Music payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        model: Optional. Provider model name.
        **kwargs: Optional. Workers AI fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    input_payload = {"lyrics": lyrics}
    provider_api.add_optional(input_payload, prompt=prompt)
    provider_api.merge_kwargs(input_payload, kwargs)
    return {
        "model": _cloudflare_model_name(model or DEFAULT_MODEL),
        "input": input_payload,
    }


def _cloudflare_model_name(model):
    """Return the Workers AI model identifier accepted by the REST endpoint.

    Args:
        model: Required. Public or binding-style model identifier.

    Returns:
        The REST model identifier.
    """
    text = str(model)
    return text.removeprefix("@cf/")
