"""Verify dispatcher behaviour without exercising real provider APIs."""

from __future__ import annotations

import pytest


def test_text_generate_routes_to_provider(monkeypatch):
    from easy_ai_clients import text
    from easy_ai_clients.text._apis import openai as provider

    captured = {}

    def fake_generate(input_text, instruction=None, model="gpt-5-nano", **kwargs):
        captured["input_text"] = input_text
        captured["instruction"] = instruction
        captured["model"] = model
        captured["kwargs"] = kwargs
        return {
            "request_id": "stub",
            "cost_source": "stub",
            "cost_usd": 0.0,
            "input_text": input_text,
            "output_text": "ok",
        }

    monkeypatch.setattr(provider, "generate", fake_generate)
    result = text.generate(
        "hello",
        instruction="be concise",
        model="gpt-5-nano",
        api="openai",
        temperature=0.1,
    )

    assert result["output_text"] == "ok"
    assert captured["input_text"] == "hello"
    assert captured["instruction"] == "be concise"
    assert captured["model"] == "gpt-5-nano"
    assert captured["kwargs"] == {"temperature": 0.1}


def test_audio_generate_routes_to_provider(monkeypatch):
    from easy_ai_clients import audio
    from easy_ai_clients.audio._synthesize._apis import openai as provider

    captured = {}

    def fake_generate(text, model="tts-1", voice="alloy", language_code="en", **kwargs):
        captured.update(
            text=text,
            model=model,
            voice=voice,
            language_code=language_code,
            kwargs=kwargs,
        )
        return {"cost_usd": 0.0, "audio": object(), "words": []}

    monkeypatch.setattr(provider, "generate", fake_generate)
    audio.generate(
        "hi",
        model="tts-1",
        voice="alloy",
        language_code="pt",
        api="openai",
        speed=1.1,
    )

    assert captured["text"] == "hi"
    assert captured["model"] == "tts-1"
    assert captured["voice"] == "alloy"
    assert captured["language_code"] == "pt"
    assert captured["kwargs"] == {"speed": 1.1}


def test_audio_transcribe_routes_to_provider(monkeypatch):
    from easy_ai_clients import audio
    from easy_ai_clients.audio._transcribe._apis import deepgram as provider

    captured = {}

    def fake_transcribe(audio_input, model="nova-2", **kwargs):
        captured.update(audio_input=audio_input, model=model, kwargs=kwargs)
        return {"text": "ok"}

    monkeypatch.setattr(provider, "transcribe", fake_transcribe)
    audio.transcribe("audio.mp3", model="nova-2", api="deepgram", language="en")

    assert captured["audio_input"] == "audio.mp3"
    assert captured["model"] == "nova-2"
    assert captured["kwargs"] == {"language": "en"}


@pytest.mark.parametrize("op", ["generate", "edit", "remix", "analyze"])
def test_image_dispatcher_routes_to_provider(monkeypatch, op):
    from easy_ai_clients import image
    from easy_ai_clients.image._analyze._apis import openai as analyze_provider
    from easy_ai_clients.image._edit._apis import openai as edit_provider
    from easy_ai_clients.image._generate._apis import openai as gen_provider
    from easy_ai_clients.image._remix._apis import openai as remix_provider

    captured = {}

    if op == "generate":
        def fake(prompt, model="gpt-image-1-mini", **kwargs):
            captured.update(prompt=prompt, model=model, kwargs=kwargs)
            return {"cust_usd": 0, "base64": "", "warnings": "", "request_id": ""}

        monkeypatch.setattr(gen_provider, "generate", fake)
        image.generate("a cat", api="openai", size="1024x1024")
    elif op == "edit":
        def fake(prompt, image_input, model="gpt-image-1-mini", **kwargs):
            captured.update(prompt=prompt, image=image_input, model=model, kwargs=kwargs)
            return {"cust_usd": 0, "base64": "", "warnings": "", "request_id": ""}

        monkeypatch.setattr(edit_provider, "edit", fake)
        image.edit("a cat", "src.png", api="openai", size="1024x1024")
    elif op == "remix":
        def fake(prompt, reference_images, **kwargs):
            captured.update(prompt=prompt, references=reference_images, kwargs=kwargs)
            return {"cust_usd": 0, "base64": "", "warnings": "", "request_id": ""}

        monkeypatch.setattr(remix_provider, "remix", fake)
        image.remix("a cat", ["ref.png"], api="openai", model="gpt-image-1-mini")
    else:
        def fake(prompt, image_input, model="gpt-4.1-nano", **kwargs):
            captured.update(prompt=prompt, image=image_input, model=model, kwargs=kwargs)
            return {"request_id": "", "cost_usd": 0.0, "input_text": prompt, "output": ""}

        monkeypatch.setattr(analyze_provider, "analyze", fake)
        image.analyze("describe", "src.png", api="openai", model="gpt-4.1-nano")

    assert "kwargs" in captured


def test_text_update_cost_unsupported():
    from easy_ai_clients import text

    with pytest.raises(NotImplementedError):
        text.update_cost({}, api="anthropic")
