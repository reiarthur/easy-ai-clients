from easy_ai_clients.music._audio_to_music._apis import deapi as audio_deapi
from easy_ai_clients.music._audio_to_music._apis import falai as audio_falai
from easy_ai_clients.music._audio_to_music._apis import generatesongs as audio_generatesongs
from easy_ai_clients.music._audio_to_music._apis import runware as audio_runware
from easy_ai_clients.music._edit._apis import falai as edit_falai
from easy_ai_clients.music._edit._apis import topmediai as edit_topmediai
from easy_ai_clients.music._lyrics_to_song._apis import cloudflare as lyrics_cloudflare
from easy_ai_clients.music._lyrics_to_song._apis import falai as lyrics_falai
from easy_ai_clients.music._lyrics_to_song._apis import novita as lyrics_novita
from easy_ai_clients.music._lyrics_to_song._apis import replicate as lyrics_replicate
from easy_ai_clients.music._lyrics_to_song._apis import runware as lyrics_runware
from easy_ai_clients.music._lyrics_to_song._apis import segmind as lyrics_segmind
from easy_ai_clients.music._media_to_music._apis import elevenlabs as media_elevenlabs
from easy_ai_clients.music._media_to_music._apis import google as media_google
from easy_ai_clients.music._stem_separation._apis import beatoven as stems_beatoven
from easy_ai_clients.music._stem_separation._apis import soundverse as stems_soundverse
from easy_ai_clients.music._text_to_music._apis import cloudflare as text_cloudflare
from easy_ai_clients.music._text_to_music._apis import deapi as text_deapi
from easy_ai_clients.music._text_to_music._apis import elevenlabs as text_elevenlabs
from easy_ai_clients.music._text_to_music._apis import generatesongs as text_generatesongs
from easy_ai_clients.music._text_to_music._apis import minimax as text_minimax
from easy_ai_clients.music._text_to_music._apis import musicful as text_musicful
from easy_ai_clients.music._text_to_music._apis import topmediai as text_topmediai
from easy_ai_clients.music._voice_conversion._apis import generatesongs as voice_generatesongs
from easy_ai_clients.music._voice_conversion._apis import musicfy as voice_musicfy


def test_text_to_music_elevenlabs_payload_forwards_safe_direct_rest_kwargs():
    payload = text_elevenlabs._build_payload(
        "music_v1",
        {"prompt": "Lo-fi piano loop"},
        {
            "music_length_ms": 30000,
            "output_format": "mp3_44100_128",
            "genre_tags": ["lofi", "piano"],
            "timeout": 5,
            "api_key": "secret",
        },
    )

    assert payload["prompt"] == "Lo-fi piano loop"
    assert payload["model"] == "music_v1"
    assert payload["music_length_ms"] == 30000
    assert payload["output_format"] == "mp3_44100_128"
    assert payload["genre_tags"] == ["lofi", "piano"]
    assert "timeout" not in payload
    assert "api_key" not in payload


def test_lyrics_to_song_segmind_payload_forwards_marketplace_kwargs():
    payload = lyrics_segmind._build_payload(
        "[Verse]\nHello from a smoke test",
        prompt="synthwave ballad",
        model="ace-step-music",
        output_seconds=30,
        guidance_scale=3.5,
        future_marketplace_option="kept",
    )

    assert payload["lyrics"] == "[Verse]\nHello from a smoke test"
    assert payload["genres"] == "synthwave ballad"
    assert payload["output_seconds"] == 30
    assert payload["guidance_scale"] == 3.5
    assert payload["future_marketplace_option"] == "kept"


def test_lyrics_to_song_novita_payload_forwards_hosted_minimax_kwargs():
    payload = lyrics_novita._build_payload(
        "[Verse]\nTiny test song",
        prompt="acoustic pop",
        model="music-2.5+",
        aigc_watermark=False,
        audio_setting={"format": "mp3", "sample_rate": 44100},
    )

    assert payload["model"] == "music-2.5+"
    assert payload["lyrics"] == "[Verse]\nTiny test song"
    assert payload["prompt"] == "acoustic pop"
    assert payload["aigc_watermark"] is False
    assert "watermark" not in payload
    assert payload["audio_setting"] == {"format": "mp3", "sample_rate": 44100}


def test_lyrics_to_song_novita_accepts_watermark_alias():
    payload = lyrics_novita._build_payload(
        "[Verse]\nTiny test song",
        prompt="acoustic pop",
        model="music-2.5+",
        watermark=True,
    )

    assert payload["aigc_watermark"] is True
    assert "watermark" not in payload


def test_lyrics_to_song_replicate_rejects_nested_lyrics_override():
    try:
        lyrics_replicate._build_payload(
            "[Verse]\nPublic lyrics",
            input={"lyrics": "[Verse]\nNested lyrics"},
        )
    except ValueError as exc:
        assert "public lyrics argument" in str(exc)
    else:
        raise AssertionError("Expected nested lyrics override to be rejected.")


def test_lyrics_to_song_runware_rejects_nested_lyrics_override():
    try:
        lyrics_runware._build_payload(
            "[Verse]\nPublic lyrics",
            settings={"lyrics": "[Verse]\nNested lyrics"},
        )
    except ValueError as exc:
        assert "public lyrics argument" in str(exc)
    else:
        raise AssertionError("Expected nested lyrics override to be rejected.")


def test_lyrics_to_song_cloudflare_payload_uses_model_input_wrapper():
    payload = lyrics_cloudflare._build_payload(
        "[Verse]\nTiny test song",
        prompt="acoustic pop",
        model="@cf/minimax/music-2.6",
        is_instrumental=False,
        lyrics_optimizer=False,
    )

    assert payload["model"] == "minimax/music-2.6"
    assert payload["input"]["lyrics"] == "[Verse]\nTiny test song"
    assert payload["input"]["prompt"] == "acoustic pop"
    assert payload["input"]["is_instrumental"] is False
    assert payload["input"]["lyrics_optimizer"] is False


def test_media_to_music_elevenlabs_keeps_multiple_local_files():
    data, files, close_files, metadata = media_elevenlabs._build_payload(
        [b"first-video", b"second-video"],
        prompt="cinematic",
        model="music_v1",
    )

    try:
        assert data["prompt"] == "cinematic"
        assert data["model_id"] == "music_v1"
        assert [name for name, _file in files] == ["videos", "videos"]
        assert len(files) == 2
        assert len(metadata["input_media"]) == 2
    finally:
        close_files()


def test_text_to_music_deapi_payload_uses_current_v2_defaults():
    payload = text_deapi._build_payload(
        "ACE-Step-v1.5-turbo",
        {"prompt": "energetic synth hook"},
        {},
    )

    assert payload["caption"] == "energetic synth hook"
    assert payload["model"] == "ACE-Step-v1.5-turbo"
    assert payload["lyrics"] == "[Instrumental]"
    assert payload["duration"] == 30
    assert payload["inference_steps"] == 8
    assert payload["guidance_scale"] == 7


def test_text_to_music_cloudflare_payload_wraps_input():
    payload = text_cloudflare._build_payload(
        "@cf/minimax/music-2.6",
        {"prompt": "short cinematic sting", "format": "mp3"},
        {},
    )

    assert payload["model"] == "minimax/music-2.6"
    assert payload["input"] == {
        "prompt": "short cinematic sting",
        "format": "mp3",
    }


def test_text_to_music_generatesongs_style_overrides_prompt_field():
    payload = text_generatesongs._build_payload(
        "songs-generate",
        {"prompt": "bright synth pop", "style": "cinematic rock"},
        {},
    )

    assert payload["style"] == "cinematic rock"
    assert "prompt" not in payload


def test_text_to_music_musicful_style_overrides_prompt_field():
    payload = text_musicful._build_payload(
        "MFV3.0",
        {"prompt": "bright synth pop", "style": "cinematic rock"},
        {},
    )

    assert payload["style"] == "cinematic rock"
    assert payload["action"] == "auto"
    assert payload["mv"] == "MFV3.0"
    assert "prompt" not in payload


def test_text_to_music_minimax_forwards_stream_flag():
    payload = text_minimax._build_payload(
        "music-2.6",
        {"prompt": "short cinematic sting"},
        {"stream": True},
    )

    assert payload["stream"] is True


def test_falai_queue_result_endpoints_use_response_suffix(monkeypatch):
    assert lyrics_falai.RESULT_ENDPOINT.endswith("/requests/{request_id}/response")

    captured = {}

    def request_json(method, url, headers=None, timeout=60, retries=2):
        captured["method"] = method
        captured["url"] = url
        return {
            "status": "completed",
            "audio_url": "https://cdn.example.com/song.mp3",
        }

    monkeypatch.setenv("FAL_KEY", "fake-key")
    monkeypatch.setattr(audio_falai.http_utils, "request_json", request_json)

    audio_falai.get_generation_result("request-1", model=audio_falai.DEFAULT_MODEL)

    assert captured["method"] == "GET"
    assert captured["url"].endswith("/requests/request-1/response")


def test_audio_to_music_deapi_default_status_endpoint_is_v2():
    endpoint = audio_deapi._format_endpoint(
        audio_deapi.DEFAULT_STATUS_ENDPOINT,
        "request-1",
    )

    assert endpoint == "https://api.deapi.ai/api/v2/jobs/request-1"


def test_media_to_music_google_payload_uses_visual_media_and_metadata():
    payload, metadata = media_google._build_payload(
        "https://example.com/poster.png",
        prompt="cinematic orchestral theme",
        model="lyria-3-pro-preview",
        candidate_count=1,
    )

    parts = payload["contents"][0]["parts"]
    assert parts[0] == {"text": "cinematic orchestral theme"}
    assert parts[1]["fileData"]["fileUri"] == "https://example.com/poster.png"
    assert parts[1]["fileData"]["mimeType"] == "image/png"
    assert payload["candidate_count"] == 1
    assert metadata["input_media"][0]["kind"] == "url"
    assert metadata["input_media"][0]["source_url"] == "https://example.com/poster.png"


def test_audio_to_music_runware_payload_uses_audio_reference_and_settings():
    payload = audio_runware._build_payload(
        "https://example.com/reference.wav",
        prompt="remix into dance pop",
        model="runware:ace-step@v1.5-turbo",
        taskUUID="task-1",
        duration=45,
        numberResults=2,
        lyrics="[Verse]\nDance test",
        bpm=128,
        customControl="future",
        timeout=5,
    )

    assert payload["taskType"] == "audioInference"
    assert payload["taskUUID"] == "task-1"
    assert payload["model"] == "runware:ace-step@v1.5-turbo"
    assert payload["positivePrompt"] == "remix into dance pop"
    assert payload["inputs"] == {"audio": "https://example.com/reference.wav"}
    assert payload["settings"]["lyrics"] == "[Verse]\nDance test"
    assert payload["settings"]["bpm"] == 128
    assert payload["duration"] == 45
    assert payload["numberResults"] == 2
    assert payload["customControl"] == "future"
    assert "timeout" not in payload


def test_audio_to_music_generatesongs_uses_official_upload_endpoint():
    assert audio_generatesongs.DEFAULT_UPLOAD_ENDPOINT.endswith("/files/upload")


def test_edit_falai_payload_uses_reference_audio_and_forwards_model_fields():
    payload = edit_falai._build_payload(
        "https://example.com/source.wav",
        prompt="extend the chorus",
        model_id="fal-ai/music-edit",
        repainting_start=12,
        repainting_end=24,
        timeout=5,
    )

    assert payload["prompt"] == "extend the chorus"
    assert payload["reference_audio"] == "https://example.com/source.wav"
    assert payload["repainting_start"] == 12
    assert payload["repainting_end"] == 24
    assert "model_id" not in payload
    assert "timeout" not in payload


def test_edit_topmediai_status_uses_default_base_url_and_ids_param(monkeypatch):
    captured = {}

    monkeypatch.setattr(edit_topmediai, "_headers", lambda kwargs: {"x-api-key": "fake"})

    def fake_get_json(endpoint, headers=None, params=None, **kwargs):
        captured["endpoint"] = endpoint
        captured["params"] = params
        return {"status": "completed", "audio_url": "https://cdn.example.com/song.mp3"}

    monkeypatch.setattr(edit_topmediai._ops, "get_json", fake_get_json)

    result = edit_topmediai.get_generation_status("task-1")

    assert captured["endpoint"] == "https://api.topmediai.com/v3/music/tasks"
    assert captured["params"] == {"ids": "task-1"}
    assert result["status"] == "completed"


def test_stem_separation_beatoven_payload_uses_stems_audio_url():
    payload = stems_beatoven._build_payload(
        "https://example.com/song.mp3",
        model="maestro-v2",
        stem_count=4,
        timeout=5,
    )

    assert payload["model"] == "maestro-v2"
    assert payload["audio_url"] == "https://example.com/song.mp3"
    assert payload["stem_count"] == 4
    assert "timeout" not in payload


def test_stem_separation_soundverse_payload_uses_audio_url_key():
    payload = stems_soundverse._build_payload(
        "https://example.com/song.mp3",
        stem_type="all-stems",
        timeout=5,
    )

    assert payload["audioUrl"] == "https://example.com/song.mp3"
    assert "audio_url" not in payload
    assert "timeout" not in payload


def test_text_to_music_topmediai_payload_uses_style_not_prompt():
    payload = text_topmediai._build_payload(
        "v4.5-plus",
        {"prompt": "bright synth pop"},
        {"action": "auto"},
    )

    assert payload["action"] == "auto"
    assert payload["style"] == "bright synth pop"
    assert "prompt" not in payload


def test_voice_conversion_musicfy_payload_uses_voice_and_audio_url():
    payload = voice_musicfy._build_payload(
        "https://example.com/vocal.wav",
        voice="voice-1",
        prompt="clean vocal take",
        pitch_shift=2,
        timeout=5,
    )

    assert payload["prompt"] == "clean vocal take"
    assert payload["voice_id"] == "voice-1"
    assert payload["audio_url"] == "https://example.com/vocal.wav"
    assert payload["pitch_shift"] == 2
    assert "timeout" not in payload


def test_voice_conversion_generatesongs_uses_non_gender_voice_as_vocal_file_id():
    payload = voice_generatesongs._build_payload(
        "source-vocal-file",
        voice="voice-123",
        prompt="clean vocal take",
    )

    assert payload["style"] == "clean vocal take"
    assert payload["vocalFileId"] == "voice-123"
    assert "vocalGender" not in payload
