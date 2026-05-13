"""Smoke tests asserting that every public dispatcher and provider imports."""

from __future__ import annotations

import importlib

import pytest


def test_top_level_exports():
    import easy_ai_clients

    assert hasattr(easy_ai_clients, "text")
    assert hasattr(easy_ai_clients, "audio")
    assert hasattr(easy_ai_clients, "image")
    assert hasattr(easy_ai_clients, "video")
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
    assert callable(audio.update_cost)
    assert isinstance(audio.available_synthesize_apis(), tuple)
    assert isinstance(audio.available_transcribe_apis(), tuple)


def test_image_dispatchers_callable():
    from easy_ai_clients import image

    assert callable(image.generate)
    assert callable(image.edit)
    assert callable(image.remix)
    assert callable(image.analyze)


def test_video_dispatchers_callable():
    from easy_ai_clients import video

    assert callable(video.generate)
    assert callable(video.text_to_video)
    assert callable(video.image_to_video)
    assert callable(video.motion_control)
    assert callable(video.image_lipsync)
    assert callable(video.video_lipsync)
    assert callable(video.get_status)
    assert callable(video.get_result)
    assert callable(video.download)
    assert isinstance(video.available_text_to_video_apis(), tuple)
    assert isinstance(video.available_image_to_video_apis(), tuple)
    assert isinstance(video.available_motion_control_apis(), tuple)
    assert isinstance(video.available_image_lipsync_apis(), tuple)
    assert isinstance(video.available_video_lipsync_apis(), tuple)


@pytest.mark.parametrize(
    ("modality", "operation", "providers"),
    [
        ("text", "_apis", (
            "anthropic", "cohere", "deepinfra", "deepseek", "falai", "fireworks",
            "google", "groq", "huggingface", "mistral", "openai", "openrouter",
            "together", "xai",
        )),
        ("audio", "_synthesize._apis", (
            "deepinfra", "elevenlabs", "google", "mistral",
            "openai", "together", "xai",
        )),
        ("audio", "_transcribe._apis", (
            "deepgram", "elevenlabs", "falai", "fireworks",
            "speechmatics", "together",
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
        ("video", "_text_to_video._apis", ("falai", "google", "runway")),
        ("video", "_image_to_video._apis", ("falai", "google", "runway")),
        ("video", "_motion_control._apis", ("falai", "runway")),
        ("video", "_image_lipsync._apis", ("falai",)),
        ("video", "_video_lipsync._apis", ("falai",)),
    ],
)
def test_provider_modules_import(modality, operation, providers):
    for provider in providers:
        importlib.import_module(
            f"easy_ai_clients.{modality}.{operation}.{provider}"
        )


def test_unknown_api_raises():
    from easy_ai_clients import audio, image, text, video

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
    with pytest.raises(ValueError):
        video.generate("hi", api="bogus")
    with pytest.raises(ValueError):
        video.image_to_video("hi", "img.png", api="bogus")
    with pytest.raises(ValueError):
        video.motion_control(image="img.png", video="motion.mp4", api="bogus")
    with pytest.raises(ValueError):
        video.image_lipsync(image="img.png", audio="voice.wav", api="bogus")
    with pytest.raises(ValueError):
        video.video_lipsync(video="speaker.mp4", audio="voice.wav", api="bogus")


def test_missing_api_raises():
    from easy_ai_clients import text

    with pytest.raises(TypeError):
        text.generate("hi")  # type: ignore[call-arg]
