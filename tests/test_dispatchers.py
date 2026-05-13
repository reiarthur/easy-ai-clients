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


def test_text_generate_routes_to_falai_provider(monkeypatch):
    from easy_ai_clients import text
    from easy_ai_clients.text._apis import falai as provider

    captured = {}

    def fake_generate(input_text, instruction=None, model="google/gemini-2.5-flash", **kwargs):
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
    result = text.generate("hello", model="demo/model", api="falai", temperature=0.1)

    assert result["output_text"] == "ok"
    assert captured["input_text"] == "hello"
    assert captured["model"] == "demo/model"
    assert captured["kwargs"] == {"temperature": 0.1}


def test_text_old_fal_identifier_rejected():
    from easy_ai_clients import text

    assert "falai" in text.available_apis()
    assert "fal" not in text.available_apis()
    with pytest.raises(ValueError):
        text.generate("hello", api="fal")


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


def test_audio_update_cost_dispatcher_errors():
    from easy_ai_clients import audio

    with pytest.raises(NotImplementedError):
        audio.update_cost("transcribe", {"text": "ok"}, api="fireworks")

    with pytest.raises(ValueError):
        audio.update_cost("generate", {"text": "ok"}, api="deepgram")


def test_removed_revai_transcription_identifier_rejected():
    from easy_ai_clients import audio

    assert audio.available_transcribe_apis() == (
        "deepgram",
        "elevenlabs",
        "falai",
        "fireworks",
        "speechmatics",
        "together",
    )
    with pytest.raises(ValueError):
        audio.transcribe("audio.mp3", api="revai")


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


@pytest.mark.parametrize(
    ("op", "provider_module", "function_name", "call"),
    [
        (
            "text_to_video",
            "easy_ai_clients.video._text_to_video._apis.google",
            "generate_text_to_video",
            lambda video: video.text_to_video(
                "a product shot",
                api="google",
                model="veo-demo",
                duration_seconds=4,
            ),
        ),
        (
            "image_to_video",
            "easy_ai_clients.video._image_to_video._apis.runway",
            "generate_image_to_video",
            lambda video: video.image_to_video(
                "animate this",
                "image.png",
                api="runway",
                model="gen-demo",
                duration=5,
            ),
        ),
        (
            "motion_control",
            "easy_ai_clients.video._motion_control._apis.falai",
            "generate_motion_control",
            lambda video: video.motion_control(
                image="character.png",
                video="motion.mp4",
                api="falai",
                character_orientation="image",
                duration_seconds=5,
            ),
        ),
        (
            "image_lipsync",
            "easy_ai_clients.video._image_lipsync._apis.falai",
            "generate_image_lipsync",
            lambda video: video.image_lipsync(
                image="avatar.png",
                audio="voice.wav",
                api="falai",
                resolution="480p",
            ),
        ),
        (
            "video_lipsync",
            "easy_ai_clients.video._video_lipsync._apis.falai",
            "generate_video_lipsync",
            lambda video: video.video_lipsync(
                video="speaker.mp4",
                audio="voice.wav",
                api="falai",
                duration_seconds=5,
            ),
        ),
    ],
)
def test_video_dispatcher_routes_to_provider(monkeypatch, op, provider_module, function_name, call):
    import importlib

    from easy_ai_clients import video

    provider = importlib.import_module(provider_module)
    captured = {}

    def fake(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {
            "provider": "stub",
            "model": kwargs.get("model", "stub"),
            "status": "completed",
            "request_id": "request",
            "video_url": "https://example.com/video.mp4",
            "output_path": None,
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "stub",
            "raw_response": {},
        }

    monkeypatch.setattr(provider, function_name, fake)
    result = call(video)

    assert result["status"] == "completed"
    assert captured["kwargs"]
    if op == "image_to_video":
        assert captured["kwargs"]["image_path"] == "image.png"
    if op == "motion_control":
        assert captured["kwargs"]["image_path"] == "character.png"
        assert captured["kwargs"]["video_path"] == "motion.mp4"
    if op == "image_lipsync":
        assert captured["kwargs"]["image_path"] == "avatar.png"
        assert captured["kwargs"]["audio_path"] == "voice.wav"
    if op == "video_lipsync":
        assert captured["kwargs"]["video_path"] == "speaker.mp4"
        assert captured["kwargs"]["audio_path"] == "voice.wav"


def test_video_async_helpers_route_to_provider(monkeypatch):
    from easy_ai_clients import video
    from easy_ai_clients.video._text_to_video._apis import google as provider

    captured = {}

    def fake_status(request_id, **kwargs):
        captured["status"] = (request_id, kwargs)
        return {"status": "running"}

    def fake_result(request_id, output_path=None, **kwargs):
        captured["result"] = (request_id, output_path, kwargs)
        return {"status": "completed", "output_path": output_path}

    def fake_download(request_id=None, video_url=None, output_path=None, **kwargs):
        captured["download"] = (request_id, video_url, output_path, kwargs)
        return output_path

    monkeypatch.setattr(provider, "get_generation_status", fake_status)
    monkeypatch.setattr(provider, "get_generation_result", fake_result)
    monkeypatch.setattr(provider, "download_generation", fake_download)

    assert video.get_status("text_to_video", "op-1", api="google")["status"] == "running"
    assert (
        video.get_result("text_to_video", "op-1", output_path="out.mp4", api="google")[
            "output_path"
        ]
        == "out.mp4"
    )
    assert video.download("text_to_video", video_url="https://example.com/v.mp4", output_path="out.mp4", api="google") == "out.mp4"
    assert captured["status"][0] == "op-1"
    assert captured["result"][1] == "out.mp4"
    assert captured["download"][1] == "https://example.com/v.mp4"


def test_google_text_to_video_validates_current_veo_limits():
    from easy_ai_clients.video._text_to_video._apis import google as provider

    with pytest.raises(ValueError, match="person_generation"):
        provider.generate_text_to_video("a product shot", person_generation="allow_adult")

    with pytest.raises(ValueError, match="number_of_videos"):
        provider.generate_text_to_video("a product shot", number_of_videos=2)

    with pytest.raises(ValueError, match="duration_seconds=8"):
        provider.generate_text_to_video(
            "a product shot",
            duration_seconds=4,
            resolution="1080p",
        )

    with pytest.raises(ValueError, match="Unsupported parameter"):
        provider.generate_text_to_video("a product shot", negative_prompt="no text")


def test_google_image_to_video_validates_current_veo_limits_and_payload_shape():
    from easy_ai_clients.video._image_to_video._apis import google as provider

    with pytest.raises(ValueError, match="person_generation"):
        provider.generate_image_to_video(
            "animate this",
            image_url="https://example.com/image.png",
            person_generation="allow_all",
        )

    with pytest.raises(ValueError, match="number_of_videos"):
        provider.generate_image_to_video(
            "animate this",
            image_url="https://example.com/image.png",
            number_of_videos=2,
        )

    payload = provider._build_payload(  # noqa: SLF001
        provider.DEFAULT_MODEL,
        {
            "prompt": "animate this",
            "image": "data:image/png;base64,first",
            "output_path": None,
        },
        {"last_image_url": "data:image/png;base64,last"},
    )

    assert payload["instances"][0]["image"] == {
        "inlineData": {"mimeType": "image/png", "data": "first"}
    }
    assert payload["instances"][0]["lastFrame"] == {
        "inlineData": {"mimeType": "image/png", "data": "last"}
    }


def test_falai_video_lipsync_validates_current_frame_range():
    from easy_ai_clients.video._video_lipsync._apis import falai as provider

    provider._build_payload(  # noqa: SLF001
        provider.DEFAULT_MODEL,
        {
            "video": "https://example.com/source.mp4",
            "audio": "https://example.com/voice.wav",
            "output_path": None,
        },
        {"num_frames": 145},
    )

    with pytest.raises(ValueError, match="41 to 241"):
        provider.generate_video_lipsync(
            video_url="https://example.com/source.mp4",
            audio_url="https://example.com/voice.wav",
            num_frames=40,
        )

    with pytest.raises(ValueError, match="41 to 241"):
        provider.generate_video_lipsync(
            video_url="https://example.com/source.mp4",
            audio_url="https://example.com/voice.wav",
            num_frames=242,
        )


def test_falai_text_to_video_validates_current_frame_rate_range():
    from easy_ai_clients.video._text_to_video._apis import falai as provider

    with pytest.raises(ValueError, match="4 to 60"):
        provider.generate_text_to_video("a product shot", frames_per_second=120)


def test_video_extract_video_url_accepts_falai_string_shapes():
    from easy_ai_clients.video._shared import extract_video_url

    assert extract_video_url({"video": "https://example.com/video.mp4"}) == (
        "https://example.com/video.mp4"
    )
    assert extract_video_url({"videos": ["https://example.com/video.mp4"]}) == (
        "https://example.com/video.mp4"
    )


def test_text_update_cost_unsupported():
    from easy_ai_clients import text

    with pytest.raises(NotImplementedError):
        text.update_cost({}, api="anthropic")
