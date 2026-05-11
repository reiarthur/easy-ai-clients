"""Audio dispatcher.

Exposes :func:`generate` for text-to-speech, :func:`transcribe` for
speech-to-text, and :func:`update_cost` for supported post-hoc audio cost
refreshes. The provider is selected via the ``api`` keyword argument and must
match the file name (without ``.py``) of an internal provider module.

Last updated: 2026-04-25
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "generate",
    "transcribe",
    "update_cost",
    "available_synthesize_apis",
    "available_transcribe_apis",
]


_SYNTHESIZE_APIS = (
    "deepinfra",
    "elevenlabs",
    "google",
    "mistral",
    "openai",
    "together",
    "xai",
)

_TRANSCRIBE_APIS = (
    "deepgram",
    "elevenlabs",
    "falai",
    "fireworks",
    "speechmatics",
    "together",
)


def available_synthesize_apis():
    """Return the tuple of supported synthesis provider identifiers."""

    return _SYNTHESIZE_APIS


def available_transcribe_apis():
    """Return the tuple of supported transcription provider identifiers."""

    return _TRANSCRIBE_APIS


def _load_synthesize(api):
    if not isinstance(api, str) or not api:
        raise ValueError(
            "audio.generate(...) requires the keyword argument 'api'. "
            f"Available APIs: {', '.join(_SYNTHESIZE_APIS)}."
        )
    if api not in _SYNTHESIZE_APIS:
        raise ValueError(
            f"Unknown audio synthesis API '{api}'. Available APIs: "
            f"{', '.join(_SYNTHESIZE_APIS)}."
        )
    return importlib.import_module(f"._synthesize._apis.{api}", __name__)


def _load_transcribe(api):
    if not isinstance(api, str) or not api:
        raise ValueError(
            "audio.transcribe(...) requires the keyword argument 'api'. "
            f"Available APIs: {', '.join(_TRANSCRIBE_APIS)}."
        )
    if api not in _TRANSCRIBE_APIS:
        raise ValueError(
            f"Unknown audio transcription API '{api}'. Available APIs: "
            f"{', '.join(_TRANSCRIBE_APIS)}."
        )
    return importlib.import_module(f"._transcribe._apis.{api}", __name__)


def generate(text, model=None, voice=None, language_code="en", *, api, **kwargs):
    """Synthesize speech with the selected provider.

    ### Parameters:
    - text (str): Input text to synthesize.
    - model (str | None): Provider-specific model identifier. When omitted, the
      provider default is used.
    - voice (str | None): Provider-specific voice identifier. When omitted, the
      provider default is used.
    - language_code (str): BCP-47 language code used by the provider.
    - api (str): Provider identifier listed by :func:`available_synthesize_apis`.
    - **kwargs: Extra provider-native parameters.

    ### Returns:
    - dict: Provider-normalized audio result with `cost_usd`, `audio` and
      `words` fields.
    """

    module = _load_synthesize(api)
    arguments: dict[str, Any] = {"language_code": language_code, **kwargs}
    if model is not None:
        arguments["model"] = model
    if voice is not None:
        arguments["voice"] = voice
    return module.generate(text, **arguments)


def transcribe(audio_input, model=None, *, api, **kwargs):
    """Transcribe audio with the selected provider.

    ### Parameters:
    - audio_input: Path, URL, bytes, base64 string, or `pydub.AudioSegment`.
    - model (str | None): Provider-specific model identifier. When omitted, the
      provider default is used.
    - api (str): Provider identifier listed by :func:`available_transcribe_apis`.
    - **kwargs: Extra provider-native parameters.

    ### Returns:
    - dict: Normalized transcription bundle with transcript data and explicit
      cost metadata.
    """

    module = _load_transcribe(api)
    if model is None:
        return module.transcribe(audio_input, **kwargs)
    return module.transcribe(audio_input, model=model, **kwargs)


def update_cost(operation, result, *, api):
    """Refresh cost metadata for an audio result when the provider supports it."""

    if operation != "transcribe":
        raise ValueError("audio.update_cost currently supports operation='transcribe' only.")

    module = _load_transcribe(api)
    if not hasattr(module, "update_cost"):
        raise NotImplementedError(
            f"audio.update_cost is not implemented for operation='transcribe' and api='{api}'."
        )
    return module.update_cost(result)
