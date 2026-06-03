import importlib

from .._error_utils import attach_error
from ._common import media_utils, provider_utils, result_utils

_TEXT_TO_MUSIC_APIS = (
    "google", "elevenlabs", "stability", "beatoven", "musicfy", "minimax",
    "sonauto", "jen", "musicgpt", "topmediai", "modelslab", "segmind",
    "falai", "replicate", "generatesongs", "soundverse", "scenario",
    "musicful", "deapi", "runware", "novita", "cloudflare",
)

_LYRICS_TO_SONG_APIS = (
    "google", "elevenlabs", "minimax", "sonauto", "musicgpt", "topmediai",
    "segmind", "falai", "replicate", "generatesongs", "wavespeedai",
    "soundverse", "musicful", "deapi", "runware", "novita", "cloudflare",
)

_MEDIA_TO_MUSIC_APIS = ("google", "elevenlabs", "musicgpt")

_AUDIO_TO_MUSIC_APIS = (
    "stability", "musicfy", "minimax", "sonauto", "musicgpt", "topmediai",
    "modelslab", "falai", "replicate", "generatesongs", "wavespeedai",
    "soundverse", "scenario", "deapi", "runware",
)

_EDIT_APIS = (
    "stability", "sonauto", "jen", "musicgpt", "topmediai", "falai",
    "replicate", "soundverse", "scenario", "runware",
)

_STEM_SEPARATION_APIS = ("elevenlabs", "beatoven", "soundverse")

_VOICE_CONVERSION_APIS = (
    "musicfy", "musicgpt", "topmediai", "generatesongs", "soundverse",
)

_OPERATIONS = {
    "text_to_music": {
        "package": "_text_to_music",
        "function": "generate_text_to_music",
        "apis": _TEXT_TO_MUSIC_APIS,
    },
    "lyrics_to_song": {
        "package": "_lyrics_to_song",
        "function": "generate_lyrics_to_song",
        "apis": _LYRICS_TO_SONG_APIS,
    },
    "media_to_music": {
        "package": "_media_to_music",
        "function": "generate_media_to_music",
        "apis": _MEDIA_TO_MUSIC_APIS,
    },
    "audio_to_music": {
        "package": "_audio_to_music",
        "function": "generate_audio_to_music",
        "apis": _AUDIO_TO_MUSIC_APIS,
    },
    "edit": {
        "package": "_edit",
        "function": "edit_music",
        "apis": _EDIT_APIS,
    },
    "stem_separation": {
        "package": "_stem_separation",
        "function": "separate_stems",
        "apis": _STEM_SEPARATION_APIS,
        "stems": True,
    },
    "voice_conversion": {
        "package": "_voice_conversion",
        "function": "convert_voice",
        "apis": _VOICE_CONVERSION_APIS,
    },
}

_BLOCKED_SECRET_KWARGS = {
    "api_key",
    "apikey",
    "api_token",
    "access_token",
    "auth_token",
    "authorization",
    "bearer_token",
    "client_secret",
    "api_secret",
    "secret",
    "password",
    "google_api_key",
    "elevenlabs_api_key",
    "stability_api_key",
    "beatoven_api_key",
    "musicfy_api_key",
    "minimax_api_key",
    "sonauto_api_key",
    "jen_music_api_key",
    "musicgpt_api_key",
    "topmediai_api_key",
    "modelslab_api_key",
    "segmind_api_key",
    "fal_key",
    "replicate_api_token",
    "generatesongs_api_key",
    "wavespeedai_api_key",
    "soundverse_api_key",
    "scenario_api_key",
    "scenario_api_secret",
    "musicful_api_key",
    "deapi_api_key",
    "runware_api_key",
    "novita_api_key",
    "cloudflare_api_token",
}


def text_to_music(prompt, model=None, *, api, **kwargs):
    """Generate music from a prompt.

    Args:
        prompt: Required. Prompt or music brief.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific generation parameters.

    Returns:
        A normalized result dictionary.
    """
    return _dispatch_generation("text_to_music", api, model, (prompt,), kwargs)


generate = text_to_music


def lyrics_to_song(lyrics, prompt=None, model=None, *, api, **kwargs):
    """Generate a song from lyrics.

    Args:
        lyrics: Required. Lyrics, sections, or song structure.
        prompt: Optional. Additional musical prompt.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific generation parameters.

    Returns:
        A normalized result dictionary.
    """
    payload = provider_utils.add_optional(kwargs, prompt=prompt)
    return _dispatch_generation("lyrics_to_song", api, model, (lyrics,), payload)


def media_to_music(media, prompt=None, model=None, *, api, **kwargs):
    """Generate music guided by image, video, or visual media.

    Args:
        media: Required. Media input as URL, data URI, local path, or bytes.
        prompt: Optional. Additional musical prompt.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific generation parameters.

    Returns:
        A normalized result dictionary.
    """
    payload = provider_utils.add_optional(kwargs, prompt=prompt)
    return _dispatch_generation("media_to_music", api, model, (media,), payload)


def audio_to_music(audio, prompt=None, model=None, *, api, **kwargs):
    """Generate or transform music from an audio input.

    Args:
        audio: Required. Audio input as URL, data URI, local path, or bytes.
        prompt: Optional. Additional musical prompt.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific generation parameters.

    Returns:
        A normalized result dictionary.
    """
    payload = provider_utils.add_optional(kwargs, prompt=prompt)
    return _dispatch_generation("audio_to_music", api, model, (audio,), payload)


def edit(audio, prompt=None, model=None, *, api, **kwargs):
    """Edit, continue, or inpaint music from an audio input.

    Args:
        audio: Required. Audio input as URL, data URI, local path, or bytes.
        prompt: Optional. Edit instruction or continuation prompt.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific edit parameters.

    Returns:
        A normalized result dictionary.
    """
    payload = provider_utils.add_optional(kwargs, prompt=prompt)
    return _dispatch_generation("edit", api, model, (audio,), payload)


def stem_separation(audio, model=None, *, api, **kwargs):
    """Separate music into stems.

    Args:
        audio: Required. Audio input as URL, data URI, local path, or bytes.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific stem parameters.

    Returns:
        A normalized result dictionary with stems as the main output.
    """
    return _dispatch_generation("stem_separation", api, model, (audio,), kwargs)


def voice_conversion(audio, voice=None, prompt=None, model=None, *, api, **kwargs):
    """Convert or apply a singing voice to musical audio.

    Args:
        audio: Required. Audio input as URL, data URI, local path, or bytes.
        voice: Optional. Voice identifier or reference.
        prompt: Optional. Additional instruction.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific conversion parameters.

    Returns:
        A normalized result dictionary.
    """
    payload = provider_utils.add_optional(kwargs, voice=voice, prompt=prompt)
    return _dispatch_generation("voice_conversion", api, model, (audio,), payload)


def get_status(operation, request_id, model=None, *, api, **kwargs):
    """Get status for an asynchronous music generation request.

    Args:
        operation: Required. Public operation name.
        request_id: Required. Provider request ID.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific status parameters.

    Returns:
        A normalized result dictionary.
    """
    return _dispatch_async(
        operation,
        "get_generation_status",
        api,
        model,
        (request_id,),
        kwargs,
        request_id=request_id,
    )


def get_result(operation, request_id, output_path=None, model=None, *, api, **kwargs):
    """Get a result for an asynchronous music generation request.

    Args:
        operation: Required. Public operation name.
        request_id: Required. Provider request ID.
        output_path: Optional. Destination path when provider supports saving.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific result parameters.

    Returns:
        A normalized result dictionary.
    """
    payload = provider_utils.add_optional(kwargs, output_path=output_path)
    return _dispatch_async(
        operation,
        "get_generation_result",
        api,
        model,
        (request_id,),
        payload,
        request_id=request_id,
        output_path=output_path,
    )


def download(operation, request_id=None, audio_url=None, output_path=None, model=None,
             *, api, **kwargs):
    """Download a generated music result.

    Args:
        operation: Required. Public operation name.
        request_id: Optional. Provider request ID.
        audio_url: Optional. Direct audio URL to download.
        output_path: Optional. Destination path.
        model: Optional. Provider model name or identifier.
        api: Required. Lowercase provider identifier.
        **kwargs: Optional. Provider-specific download parameters.

    Returns:
        A normalized result dictionary.
    """
    provider = _normalize_api_name(api)
    config_error = _configuration_error(operation, provider)
    if config_error is not None:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=config_error,
            request_id=request_id,
            audio_url=audio_url,
            output_path=output_path,
        )

    secret_error = _secret_kwarg_error(kwargs)
    if secret_error is not None:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=secret_error,
            request_id=request_id,
            audio_url=audio_url,
            output_path=output_path,
        )

    direct_audio_url = audio_url or _direct_download_url(kwargs)

    if direct_audio_url and not output_path:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=RuntimeError("output_path is required when audio_url is provided."),
            request_id=request_id,
            audio_url=direct_audio_url,
        )

    if direct_audio_url:
        try:
            saved_path = media_utils.download_url(
                direct_audio_url,
                output_path,
                timeout=kwargs.get("download_timeout", kwargs.get("timeout", 60)),
            )
            return result_utils.normalized_result(
                provider=provider,
                operation=operation,
                model=model,
                status="completed",
                request_id=request_id,
                audio_url=direct_audio_url,
                output_path=saved_path,
            )
        except Exception as exc:
            return result_utils.failure_result(
                provider=provider,
                model=model,
                operation=operation,
                exc=exc,
                request_id=request_id,
                audio_url=direct_audio_url,
                output_path=output_path,
            )

    if not request_id:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=RuntimeError("request_id or audio_url is required for download."),
            output_path=output_path,
        )

    payload = provider_utils.add_optional(kwargs, output_path=output_path)
    return _dispatch_async(
        operation,
        "download_generation",
        provider,
        model,
        (request_id,),
        payload,
        request_id=request_id,
        output_path=output_path,
    )


def available_apis():
    """Return providers available for text-to-music generation.

    Returns:
        A tuple of provider identifiers.
    """
    return available_text_to_music_apis()


def available_text_to_music_apis():
    """Return text-to-music provider identifiers.

    Returns:
        A tuple of provider identifiers.
    """
    return _TEXT_TO_MUSIC_APIS


def available_lyrics_to_song_apis():
    """Return lyrics-to-song provider identifiers.

    Returns:
        A tuple of provider identifiers.
    """
    return _LYRICS_TO_SONG_APIS


def available_media_to_music_apis():
    """Return media-to-music provider identifiers.

    Returns:
        A tuple of provider identifiers.
    """
    return _MEDIA_TO_MUSIC_APIS


def available_audio_to_music_apis():
    """Return audio-to-music provider identifiers.

    Returns:
        A tuple of provider identifiers.
    """
    return _AUDIO_TO_MUSIC_APIS


def available_edit_apis():
    """Return music edit provider identifiers.

    Returns:
        A tuple of provider identifiers.
    """
    return _EDIT_APIS


def available_stem_separation_apis():
    """Return stem separation provider identifiers.

    Returns:
        A tuple of provider identifiers.
    """
    return _STEM_SEPARATION_APIS


def available_voice_conversion_apis():
    """Return voice conversion provider identifiers.

    Returns:
        A tuple of provider identifiers.
    """
    return _VOICE_CONVERSION_APIS


def update_cost(operation, result, *, api):
    """Update a music result with provider-specific cost metadata.

    Args:
        operation: Required. Public operation name.
        result: Required. Result dictionary to update.
        api: Required. Lowercase provider identifier.

    Returns:
        The updated result dictionary.

    Raises:
        NotImplementedError: If the provider does not support cost updates.
    """
    provider = _normalize_api_name(api)
    config_error = _configuration_error(operation, provider)
    if config_error is not None:
        if isinstance(result, dict):
            return attach_error(result, config_error, provider=provider, operation=operation)
        failure = result_utils.failure_result(
            provider=provider,
            operation=operation,
            exc=config_error,
        )
        failure["raw_response"] = result
        return failure

    module = _load_provider_module(operation, provider)
    provider_update_cost = getattr(module, "update_cost", None)
    if provider_update_cost is None:
        raise NotImplementedError(
            f"Cost updates are not implemented for provider '{provider}' and operation '{operation}'."
        )

    try:
        updated = provider_update_cost(result, operation=operation)
        return result if updated is None else updated
    except NotImplementedError:
        raise
    except Exception as exc:
        if isinstance(result, dict):
            return attach_error(result, exc, provider=provider, operation=operation)
        failure = result_utils.failure_result(
            provider=provider,
            operation=operation,
            exc=exc,
        )
        failure["raw_response"] = result
        return failure


def _dispatch_generation(operation, api, model, args, kwargs):
    """Dispatch a generation-like operation to a provider module.

    Args:
        operation: Required. Public operation name.
        api: Required. Provider identifier.
        model: Optional. Model name or identifier.
        args: Required. Positional provider arguments.
        kwargs: Required. Provider keyword arguments.

    Returns:
        A normalized result dictionary.
    """
    provider = _normalize_api_name(api)
    config_error = _configuration_error(operation, provider)
    if config_error is not None:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=config_error,
        )

    secret_error = _secret_kwarg_error(kwargs)
    if secret_error is not None:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=secret_error,
        )

    try:
        config = _OPERATIONS[operation]
        module = _load_provider_module(operation, provider)
        provider_function = getattr(module, config["function"])
        provider_kwargs = provider_utils.with_model(model, kwargs)
        raw_response = provider_function(*args, **provider_kwargs)
        return result_utils.normalize_provider_result(
            provider,
            model,
            raw_response,
            operation=operation,
            stems=config.get("stems", False),
        )
    except Exception as exc:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=exc,
        )


def _dispatch_async(operation, provider_function_name, api, model, args, kwargs,
                    request_id=None, output_path=None):
    """Dispatch an async helper operation to a provider module.

    Args:
        operation: Required. Public operation name.
        provider_function_name: Required. Provider function name.
        api: Required. Provider identifier.
        model: Optional. Model name or identifier.
        args: Required. Positional provider arguments.
        kwargs: Required. Provider keyword arguments.
        request_id: Optional. Provider request ID.
        output_path: Optional. Output path.

    Returns:
        A normalized result dictionary.
    """
    provider = _normalize_api_name(api)
    config_error = _configuration_error(operation, provider)
    if config_error is not None:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=config_error,
            request_id=request_id,
            output_path=output_path,
        )

    secret_error = _secret_kwarg_error(kwargs)
    if secret_error is not None:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=secret_error,
            request_id=request_id,
            output_path=output_path,
        )

    try:
        module = _load_provider_module(operation, provider)
    except Exception as exc:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=exc,
            request_id=request_id,
            output_path=output_path,
        )

    provider_function = getattr(module, provider_function_name, None)
    if provider_function is None:
        raise NotImplementedError(
            _missing_helper_message(provider, operation, provider_function_name)
        )

    try:
        provider_kwargs = provider_utils.with_model(model, kwargs)
        raw_response = provider_function(*args, **provider_kwargs)
        return result_utils.normalize_provider_result(
            provider,
            model,
            raw_response,
            operation=operation,
            output_path=output_path,
            stems=_OPERATIONS[operation].get("stems", False),
        )
    except NotImplementedError:
        raise
    except Exception as exc:
        return result_utils.failure_result(
            provider=provider,
            model=model,
            operation=operation,
            exc=exc,
            request_id=request_id,
            output_path=output_path,
        )


def _load_provider_module(operation, provider):
    """Load an operation-specific provider module.

    Args:
        operation: Required. Public operation name.
        provider: Required. Lowercase provider identifier.

    Returns:
        The imported provider module.
    """
    config = _OPERATIONS[operation]
    package = config["package"]
    return importlib.import_module(f".{package}._apis.{provider}", __name__)


def _direct_download_url(kwargs):
    """Return a direct downloadable URL from explicit provider references.

    Args:
        kwargs: Required. Public keyword arguments.

    Returns:
        A remote URL when one is safe to treat as media.
    """
    for key in (
        "audio_url",
        "audioUrl",
        "audioURL",
        "music_url",
        "musicUrl",
        "musicURL",
        "download_url",
        "downloadUrl",
        "flacDownloadUrl",
        "stream_url",
        "streamUrl",
        "file_url",
        "fileUrl",
    ):
        value = kwargs.get(key)
        if isinstance(value, str) and media_utils.is_remote_url(value):
            return value

    value = kwargs.get("result_url") or kwargs.get("resultUrl")
    if isinstance(value, str) and _looks_like_audio_url(value):
        return value
    return None


def _looks_like_audio_url(value):
    """Return whether a URL path looks like an audio file.

    Args:
        value: Required. Candidate URL.

    Returns:
        True when the URL has a common audio extension.
    """
    return media_utils.is_remote_url(value) and any(
        value.split("?", 1)[0].lower().endswith(suffix)
        for suffix in media_utils.AUDIO_SUFFIXES
    )


def _missing_helper_message(provider, operation, helper_name):
    """Return the standard missing helper message.

    Args:
        provider: Required. Provider identifier.
        operation: Required. Public operation name.
        helper_name: Required. Missing provider helper.

    Returns:
        A user-facing error message.
    """
    return (
        f"Provider '{provider}' does not implement '{helper_name}' "
        f"for music operation '{operation}'."
    )


def _normalize_api_name(api):
    """Normalize a public API provider value.

    Args:
        api: Required. Provider identifier.

    Returns:
        A lowercase provider identifier, or an empty string.
    """
    if not isinstance(api, str):
        if api is None:
            return ""
        api = str(api)
    return api.strip().lower()


def _configuration_error(operation, provider):
    """Return a configuration error when operation or provider is unsupported.

    Args:
        operation: Required. Public operation name.
        provider: Required. Normalized provider identifier.

    Returns:
        RuntimeError when invalid, otherwise None.
    """
    if not provider:
        return RuntimeError("api must be a non-empty provider identifier.")
    if operation not in _OPERATIONS:
        return RuntimeError(f"Unknown music operation '{operation}'.")
    if provider not in _OPERATIONS[operation]["apis"]:
        return RuntimeError(
            f"Provider '{provider}' does not support music operation '{operation}'."
        )
    return None


def _secret_kwarg_error(kwargs):
    """Return an error when public kwargs include credential-like names.

    Args:
        kwargs: Required. Public keyword arguments.

    Returns:
        RuntimeError when a secret-like parameter is present, otherwise None.
    """
    for key in kwargs:
        normalized = key.strip().lower() if isinstance(key, str) else str(key).lower()
        compact = normalized.replace("_", "").replace("-", "")
        if normalized in _BLOCKED_SECRET_KWARGS or compact in _compact_secret_kwargs():
            return RuntimeError(
                f"Credential parameter '{normalized}' is not accepted. "
                "Use the documented environment variable for the provider."
            )
        if normalized.endswith(("_api_key", "_api_token", "_api_secret")):
            return RuntimeError(
                f"Credential parameter '{normalized}' is not accepted. "
                "Use the documented environment variable for the provider."
            )
    return None


def _compact_secret_kwargs():
    """Return blocked credential names without separators.

    Returns:
        A set of compact credential-like keyword names.
    """
    return {
        name.replace("_", "").replace("-", "")
        for name in _BLOCKED_SECRET_KWARGS
    }


__all__ = (
    "generate",
    "text_to_music",
    "lyrics_to_song",
    "media_to_music",
    "audio_to_music",
    "edit",
    "stem_separation",
    "voice_conversion",
    "get_status",
    "get_result",
    "download",
    "available_apis",
    "available_text_to_music_apis",
    "available_lyrics_to_song_apis",
    "available_media_to_music_apis",
    "available_audio_to_music_apis",
    "available_edit_apis",
    "available_stem_separation_apis",
    "available_voice_conversion_apis",
    "update_cost",
)
