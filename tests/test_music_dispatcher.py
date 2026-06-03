from types import SimpleNamespace

import pytest

import easy_ai_clients
from easy_ai_clients import music

EXPECTED_APIS = {
    "text_to_music": (
        "google", "elevenlabs", "stability", "beatoven", "musicfy", "minimax",
        "sonauto", "jen", "musicgpt", "topmediai", "modelslab", "segmind",
        "falai", "replicate", "generatesongs", "soundverse", "scenario",
        "musicful", "deapi", "runware", "novita", "cloudflare",
    ),
    "lyrics_to_song": (
        "google", "elevenlabs", "minimax", "sonauto", "musicgpt", "topmediai",
        "segmind", "falai", "replicate", "generatesongs", "wavespeedai",
        "soundverse", "musicful", "deapi", "runware", "novita", "cloudflare",
    ),
    "media_to_music": ("google", "elevenlabs", "musicgpt"),
    "audio_to_music": (
        "stability", "musicfy", "minimax", "sonauto", "musicgpt", "topmediai",
        "modelslab", "falai", "replicate", "generatesongs", "wavespeedai",
        "soundverse", "scenario", "deapi", "runware",
    ),
    "edit": (
        "stability", "sonauto", "jen", "musicgpt", "topmediai", "falai",
        "replicate", "soundverse", "scenario", "runware",
    ),
    "stem_separation": ("elevenlabs", "beatoven", "soundverse"),
    "voice_conversion": (
        "musicfy", "musicgpt", "topmediai", "generatesongs", "soundverse",
    ),
}

PROVIDER_FUNCTIONS = {
    "text_to_music": "generate_text_to_music",
    "lyrics_to_song": "generate_lyrics_to_song",
    "media_to_music": "generate_media_to_music",
    "audio_to_music": "generate_audio_to_music",
    "edit": "edit_music",
    "stem_separation": "separate_stems",
    "voice_conversion": "convert_voice",
}


def _call_generation(operation, api, model="model-a"):
    if operation == "text_to_music":
        return music.text_to_music("calm piano loop", model=model, api=api, seed=11)
    if operation == "lyrics_to_song":
        return music.lyrics_to_song(
            "[Verse]\nHello world",
            prompt="indie pop",
            model=model,
            api=api,
            seed=11,
        )
    if operation == "media_to_music":
        return music.media_to_music(
            "https://example.com/scene.png",
            prompt="cinematic",
            model=model,
            api=api,
            seed=11,
        )
    if operation == "audio_to_music":
        return music.audio_to_music(
            "https://example.com/reference.wav",
            prompt="remix",
            model=model,
            api=api,
            seed=11,
        )
    if operation == "edit":
        return music.edit(
            "https://example.com/source.wav",
            prompt="extend",
            model=model,
            api=api,
            seed=11,
        )
    if operation == "stem_separation":
        return music.stem_separation(
            "https://example.com/song.mp3",
            model=model,
            api=api,
            stem_count=4,
        )
    if operation == "voice_conversion":
        return music.voice_conversion(
            "https://example.com/vocal.wav",
            voice="voice-1",
            prompt="clean vocal",
            model=model,
            api=api,
            seed=11,
        )
    raise AssertionError(f"Unsupported test operation: {operation}")


def _provider_response(operation):
    if operation == "stem_separation":
        return {
            "status": "completed",
            "stems": {"vocals": "https://cdn.example.com/vocals.wav"},
        }
    return {
        "status": "completed",
        "audio_url": f"https://cdn.example.com/{operation}.mp3",
    }


def _patch_generation_provider(monkeypatch, operation, provider):
    calls = []
    function_name = PROVIDER_FUNCTIONS[operation]

    def provider_function(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return _provider_response(operation)

    module = SimpleNamespace(**{function_name: provider_function})

    def load_provider_module(actual_operation, actual_provider):
        assert actual_operation == operation
        assert actual_provider == provider
        return module

    monkeypatch.setattr(music, "_load_provider_module", load_provider_module)
    return calls


def test_generate_aliases_text_to_music():
    assert music.generate is music.text_to_music


def test_top_level_package_exports_music_module():
    assert easy_ai_clients.music is music
    assert "music" in easy_ai_clients.__all__


@pytest.mark.parametrize("operation", tuple(EXPECTED_APIS))
def test_public_operations_route_to_provider_module_function(monkeypatch, operation):
    provider = EXPECTED_APIS[operation][0]
    calls = _patch_generation_provider(monkeypatch, operation, provider)

    result = _call_generation(operation, api=provider)

    assert len(calls) == 1
    assert result["provider"] == provider
    assert result["operation"] == operation
    assert result["model"] == "model-a"
    assert result["status"] == "completed"


@pytest.mark.parametrize("operation", tuple(EXPECTED_APIS))
def test_unknown_api_returns_normalized_failure_for_generation_calls(operation):
    result = _call_generation(operation, api="unknown-provider")

    assert result["provider"] == "unknown-provider"
    assert result["operation"] == operation
    assert result["status"] == "failed"
    assert "does not support" in result["error"]["message"]


@pytest.mark.parametrize("operation", tuple(EXPECTED_APIS))
def test_empty_api_returns_normalized_failure_for_generation_calls(operation):
    result = _call_generation(operation, api="")

    assert result["provider"] == ""
    assert result["operation"] == operation
    assert result["status"] == "failed"
    assert "non-empty provider identifier" in result["error"]["message"]


@pytest.mark.parametrize(
    "call",
    (
        lambda: music.text_to_music("prompt"),
        lambda: music.generate("prompt"),
        lambda: music.lyrics_to_song("lyrics"),
        lambda: music.media_to_music("https://example.com/image.png"),
        lambda: music.audio_to_music("https://example.com/audio.wav"),
        lambda: music.edit("https://example.com/audio.wav"),
        lambda: music.stem_separation("https://example.com/audio.wav"),
        lambda: music.voice_conversion("https://example.com/audio.wav"),
        lambda: music.get_status("text_to_music", "request-1"),
        lambda: music.get_result("text_to_music", "request-1"),
        lambda: music.download("text_to_music", request_id="request-1"),
        lambda: music.update_cost("text_to_music", {}),
    ),
)
def test_missing_required_keyword_only_api_raises_type_error(call):
    with pytest.raises(TypeError):
        call()


def test_available_api_helpers_return_exact_tuples():
    assert music.available_apis() == EXPECTED_APIS["text_to_music"]
    assert music.available_text_to_music_apis() == EXPECTED_APIS["text_to_music"]
    assert music.available_lyrics_to_song_apis() == EXPECTED_APIS["lyrics_to_song"]
    assert music.available_media_to_music_apis() == EXPECTED_APIS["media_to_music"]
    assert music.available_audio_to_music_apis() == EXPECTED_APIS["audio_to_music"]
    assert music.available_edit_apis() == EXPECTED_APIS["edit"]
    assert music.available_stem_separation_apis() == EXPECTED_APIS["stem_separation"]
    assert music.available_voice_conversion_apis() == EXPECTED_APIS["voice_conversion"]


def test_parametric_generation_is_not_exposed_as_operation():
    assert not hasattr(music, "parametric_generation")
    assert "parametric_generation" not in music.__all__
    assert "parametric_generation" not in music._OPERATIONS


def test_async_helpers_route_to_provider_helper_functions(monkeypatch):
    calls = []

    def get_generation_status(*args, **kwargs):
        calls.append(("status", args, kwargs))
        return {"status": "submitted", "request_id": args[0]}

    def get_generation_result(*args, **kwargs):
        calls.append(("result", args, kwargs))
        return {
            "status": "completed",
            "request_id": args[0],
            "audio_url": "https://cdn.example.com/result.mp3",
        }

    def download_generation(*args, **kwargs):
        calls.append(("download", args, kwargs))
        return {
            "status": "completed",
            "request_id": args[0],
            "audio_url": "https://cdn.example.com/download.mp3",
        }

    module = SimpleNamespace(
        get_generation_status=get_generation_status,
        get_generation_result=get_generation_result,
        download_generation=download_generation,
    )

    def load_provider_module(operation, provider):
        assert operation == "text_to_music"
        assert provider == "falai"
        return module

    monkeypatch.setattr(music, "_load_provider_module", load_provider_module)

    status = music.get_status(
        "text_to_music",
        "request-1",
        model="model-a",
        api="falai",
        native_option="status",
    )
    result = music.get_result(
        "text_to_music",
        "request-2",
        output_path="song.mp3",
        model="model-a",
        api="falai",
        native_option="result",
    )
    downloaded = music.download(
        "text_to_music",
        request_id="request-3",
        output_path="download.mp3",
        model="model-a",
        api="falai",
        native_option="download",
    )

    assert [call[0] for call in calls] == ["status", "result", "download"]
    assert calls[0][1] == ("request-1",)
    assert calls[0][2] == {"native_option": "status", "model": "model-a"}
    assert calls[1][1] == ("request-2",)
    assert calls[1][2] == {
        "native_option": "result",
        "output_path": "song.mp3",
        "model": "model-a",
    }
    assert calls[2][1] == ("request-3",)
    assert calls[2][2] == {
        "native_option": "download",
        "output_path": "download.mp3",
        "model": "model-a",
    }
    assert status["status"] == "submitted"
    assert result["audio_url"] == "https://cdn.example.com/result.mp3"
    assert downloaded["audio_url"] == "https://cdn.example.com/download.mp3"


def test_async_helper_missing_provider_function_raises_not_implemented(monkeypatch):
    monkeypatch.setattr(
        music,
        "_load_provider_module",
        lambda operation, provider: SimpleNamespace(),
    )

    with pytest.raises(NotImplementedError):
        music.get_status("text_to_music", "request-1", api="falai")
