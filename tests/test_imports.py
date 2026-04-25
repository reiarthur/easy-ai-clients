"""Smoke tests asserting that every public dispatcher and provider imports."""

from __future__ import annotations

import importlib

import pytest


def test_top_level_exports():
    import easy_ai_clients

    assert hasattr(easy_ai_clients, "text")
    assert hasattr(easy_ai_clients, "audio")
    assert hasattr(easy_ai_clients, "image")
    assert isinstance(easy_ai_clients.__version__, str)


def test_text_dispatcher_callable():
    from easy_ai_clients import text

    assert callable(text.generate)
    assert callable(text.list_models)
    assert callable(text.update_cost)
    assert isinstance(text.available_apis(), tuple)


def test_audio_dispatchers_callable():
    from easy_ai_clients import audio

    assert callable(audio.generate)
    assert callable(audio.transcribe)
    assert isinstance(audio.available_synthesize_apis(), tuple)
    assert isinstance(audio.available_transcribe_apis(), tuple)


def test_image_dispatchers_callable():
    from easy_ai_clients import image

    assert callable(image.generate)
    assert callable(image.edit)
    assert callable(image.remix)
    assert callable(image.analyze)


@pytest.mark.parametrize(
    ("modality", "operation", "providers"),
    [
        ("text", "_apis", (
            "anthropic", "cohere", "deepinfra", "deepseek", "fal", "fireworks",
            "google", "groq", "huggingface", "mistral", "openai", "openrouter",
            "together", "xai",
        )),
        ("audio", "_synthesize._apis", (
            "deepinfra", "elevenlabs", "google", "mistral",
            "openai", "together", "xai",
        )),
        ("audio", "_transcribe._apis", (
            "deepgram", "elevenlabs", "falai", "fireworks",
            "revai", "speechmatics", "together",
        )),
        ("image", "_generate._apis", (
            "bfl", "falai", "fireworks", "google", "openai",
            "openrouter", "stability", "together", "xai",
        )),
        ("image", "_edit._apis", (
            "bfl", "falai", "fireworks", "google", "openai",
            "openrouter", "stability", "together", "xai",
        )),
        ("image", "_remix._apis", (
            "bfl", "falai", "fireworks", "google", "openai",
            "openrouter", "stability", "together", "xai",
        )),
        ("image", "_analyze._apis", (
            "anthropic", "falai", "fireworks", "google", "groq",
            "openai", "openrouter", "together", "xai",
        )),
    ],
)
def test_provider_modules_import(modality, operation, providers):
    for provider in providers:
        importlib.import_module(
            f"easy_ai_clients.{modality}.{operation}.{provider}"
        )


def test_unknown_api_raises():
    from easy_ai_clients import audio, image, text

    with pytest.raises(ValueError):
        text.generate("hi", api="bogus")
    with pytest.raises(ValueError):
        audio.generate("hi", api="bogus")
    with pytest.raises(ValueError):
        audio.transcribe("hi.mp3", api="bogus")
    with pytest.raises(ValueError):
        image.generate("hi", api="bogus")
    with pytest.raises(ValueError):
        image.edit("hi", "img.png", api="bogus")
    with pytest.raises(ValueError):
        image.remix("hi", ["img.png"], api="bogus")
    with pytest.raises(ValueError):
        image.analyze("hi", "img.png", api="bogus")


def test_missing_api_raises():
    from easy_ai_clients import text

    with pytest.raises(TypeError):
        text.generate("hi")  # type: ignore[call-arg]
