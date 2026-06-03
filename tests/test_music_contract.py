from types import SimpleNamespace

from easy_ai_clients import music
from easy_ai_clients.music._common import cost_utils, result_utils

BASE_RESULT_KEYS = (
    "provider",
    "operation",
    "model",
    "status",
    "request_id",
    "audio_url",
    "music_url",
    "output_path",
    "audio",
    "stems",
    "cost_usd",
    "cost_currency",
    "cost_is_estimated",
    "cost_source",
    "cost_details",
    "provider_metadata",
    "raw_response",
    "warnings",
)


def test_normalized_result_keys_are_stable():
    result = result_utils.normalized_result(
        provider="unit",
        operation="text_to_music",
        model="model-a",
        status="completed",
    )

    assert tuple(result.keys()) == BASE_RESULT_KEYS


def test_audio_url_and_music_url_are_aliases():
    audio_url = "https://cdn.example.com/song.mp3"

    direct = result_utils.normalized_result(audio_url=audio_url)
    extracted = result_utils.normalize_provider_result(
        "unit",
        None,
        {"music_url": audio_url},
        operation="text_to_music",
    )

    assert direct["audio_url"] == audio_url
    assert direct["music_url"] == audio_url
    assert extracted["audio_url"] == audio_url
    assert extracted["music_url"] == audio_url


def test_normalized_outputs_redact_secret_fields_and_signed_urls():
    result = result_utils.normalize_provider_result(
        "unit",
        None,
        {
            "status": "completed",
            "audio_url": "https://cdn.example.com/song.mp3?token=secret",
            "api_key": "secret-value",
        },
        operation="text_to_music",
    )

    assert result["audio_url"] == "https://cdn.example.com/song.mp3?redacted=true"
    assert result["music_url"] == "https://cdn.example.com/song.mp3?redacted=true"
    assert result["raw_response"]["audio_url"] == (
        "https://cdn.example.com/song.mp3?redacted=true"
    )
    assert result["raw_response"]["api_key"] == "[redacted]"


def test_async_reference_urls_are_preserved_and_sanitized():
    result = result_utils.normalize_provider_result(
        "unit",
        None,
        {
            "status": "submitted",
            "request_id": "request-1",
            "status_url": "https://api.example.com/tasks/request-1",
            "poll_url": "https://api.example.com/tasks/request-1/poll",
            "download_url": "https://cdn.example.com/song.mp3?token=secret",
            "result_url": "https://cdn.example.com/song.mp3?signature=secret",
        },
        operation="text_to_music",
    )

    assert result["status_url"] == "https://api.example.com/tasks/request-1"
    assert result["poll_url"] == "https://api.example.com/tasks/request-1/poll"
    assert result["download_url"] == "https://cdn.example.com/song.mp3?redacted=true"
    assert result["result_url"] == "https://cdn.example.com/song.mp3?redacted=true"
    assert result["request_id"] == "request-1"


def test_provider_metadata_and_warnings_are_sanitized():
    result = result_utils.normalized_result(
        provider_metadata={
            "authorization": "Bearer secret-token",
            "safe_url": "https://api.example.com/task",
            "signed_url": "https://cdn.example.com/song.mp3?signature=secret",
        },
        warnings=[
            "Generated from user-provided reference.",
            "https://cdn.example.com/upload.wav?token=secret",
        ],
    )

    assert result["provider_metadata"]["authorization"] == "[redacted]"
    assert result["provider_metadata"]["safe_url"] == "https://api.example.com/task"
    assert result["provider_metadata"]["signed_url"] == (
        "https://cdn.example.com/song.mp3?redacted=true"
    )
    assert result["warnings"][0] == "Generated from user-provided reference."
    assert result["warnings"][1] == "https://cdn.example.com/upload.wav?redacted=true"


def test_stem_separation_result_uses_stems(monkeypatch):
    stems = {"vocals": "https://cdn.example.com/vocals.wav"}

    def separate_stems(*args, **kwargs):
        return {"status": "completed", "stems": stems}

    monkeypatch.setattr(
        music,
        "_load_provider_module",
        lambda operation, provider: SimpleNamespace(separate_stems=separate_stems),
    )

    result = music.stem_separation(
        "https://example.com/song.mp3",
        api="elevenlabs",
    )

    assert result["operation"] == "stem_separation"
    assert result["stems"] == stems


def test_download_requires_output_path_for_direct_url_downloads():
    result = music.download(
        "text_to_music",
        audio_url="https://cdn.example.com/song.mp3",
        api="google",
    )

    assert result["status"] == "failed"
    assert result["audio_url"] == "https://cdn.example.com/song.mp3"
    assert "output_path is required" in result["error"]["message"]


def test_download_accepts_camelcase_direct_audio_url_refs():
    result = music.download(
        "text_to_music",
        audioURL="https://cdn.example.com/song.mp3",
        api="google",
    )

    assert result["status"] == "failed"
    assert result["audio_url"] == "https://cdn.example.com/song.mp3"
    assert "output_path is required" in result["error"]["message"]


def test_text_to_music_normalization_promotes_final_audio_to_completed_with_refs():
    from easy_ai_clients.music._text_to_music import post_processing

    result = post_processing.normalize_response(
        "unit",
        "model-a",
        {
            "submit": {"status": "processing", "id": "task-1"},
            "result": {"audio_url": "https://cdn.example.com/song.mp3"},
        },
        refs={"status_url": "https://api.example.com/tasks/task-1"},
        request_id="task-1",
    )

    assert result["status"] == "completed"
    assert result["status_url"] == "https://api.example.com/tasks/task-1"
    assert result["provider_metadata"]["refs"]["status_url"] == (
        "https://api.example.com/tasks/task-1"
    )


def test_flat_stem_urls_are_preserved_as_stems():
    result = result_utils.normalize_provider_result(
        "unit",
        None,
        {
            "vocals_url": "https://cdn.example.com/vocals.wav",
            "drums_url": "https://cdn.example.com/drums.wav",
        },
        operation="stem_separation",
        stems=True,
    )

    assert result["stems"] == {
        "vocals": "https://cdn.example.com/vocals.wav",
        "drums": "https://cdn.example.com/drums.wav",
    }


def test_cost_unavailable_shape():
    cost = cost_utils.unavailable_cost_metadata()
    result = result_utils.normalized_result()

    assert cost == {
        "cost_usd": 0.0,
        "cost_currency": "USD",
        "cost_is_estimated": False,
        "cost_source": "unavailable",
        "cost_details": {},
    }
    assert result["cost_usd"] == 0.0
    assert result["cost_currency"] == "USD"
    assert result["cost_is_estimated"] is False
    assert result["cost_source"] == "unavailable"
    assert result["cost_details"] == {}


def test_estimated_cost_shape_when_local_formula_exists():
    cost = cost_utils.normalize_cost(
        0.12,
        source="official_pricing_table",
        is_estimated=True,
        details={"unit": "second", "seconds": 30},
    )
    result = result_utils.normalized_result(
        cost_usd=cost["cost_usd"],
        cost_is_estimated=cost["cost_is_estimated"],
        cost_source=cost["cost_source"],
        cost_details=cost["cost_details"],
    )

    assert cost == {
        "cost_usd": 0.12,
        "cost_currency": "USD",
        "cost_is_estimated": True,
        "cost_source": "official_pricing_table",
        "cost_details": {"unit": "second", "seconds": 30},
    }
    assert result["cost_usd"] == 0.12
    assert result["cost_currency"] == "USD"
    assert result["cost_is_estimated"] is True
    assert result["cost_source"] == "official_pricing_table"
    assert result["cost_details"] == {"unit": "second", "seconds": 30}


def test_error_redaction_for_obvious_secret_values():
    result = result_utils.failure_result(
        provider="unit",
        operation="text_to_music",
        exc=RuntimeError(
            "Authorization: Bearer sk_live_secret123 api_key=sk_live_secret456 "
            "token=plainsecret789"
        ),
    )

    message = result["error"]["message"]
    assert "sk_live_secret123" not in message
    assert "sk_live_secret456" not in message
    assert "plainsecret789" not in message
    assert "[redacted]" in message
