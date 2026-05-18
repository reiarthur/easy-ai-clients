"""Fast transcription contract tests without paid provider calls."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


class FakeResponse:
    def __init__(self, payload, headers=None):
        self._payload = payload
        self.headers = dict(headers or {})
        self.content = b"{}"

    def json(self):
        return self._payload


def _write_audio_fixture(tmp_path):
    from easy_ai_clients.audio._transcribe import pre_processing

    if pre_processing.AudioSegment is None:
        pytest.skip("pydub is required for transcription audio preparation tests")

    fixture = tmp_path / "audio.wav"
    segment = (
        pre_processing.AudioSegment.silent(duration=1000, frame_rate=44100)
        .set_channels(2)
        .set_sample_width(2)
    )
    segment.export(fixture, format="wav")
    return fixture


def _prepared_stub(
    *,
    audio=None,
    audio_bytes=b"prepared-audio",
    content_type="audio/wav",
    file_name="audio.wav",
    duration=1.0,
    upload_format="wav",
    normalized=True,
    source_format="wav",
    codec=None,
    bitrate=None,
):
    from easy_ai_clients.audio import PreparedTranscriptionAudio

    return PreparedTranscriptionAudio(
        audio=audio,
        audio_bytes=audio_bytes,
        content_type=content_type,
        file_name=file_name,
        audio_duration_seconds=duration,
        upload_format=upload_format,
        normalized=normalized,
        source_format=source_format,
        codec=codec,
        bitrate=bitrate,
    )


def _deepgram_payload(
    *,
    request_id="dg-1",
    duration=1.25,
    text="hello world",
    language="en",
    speaker=0,
):
    words = [
        {
            "word": "hello",
            "punctuated_word": "hello",
            "start": 0.0,
            "end": 0.5,
            "speaker": speaker,
        },
        {
            "word": "world",
            "punctuated_word": "world",
            "start": 0.7,
            "end": 1.2,
            "speaker": speaker,
        },
    ]
    return {
        "metadata": {"duration": duration, "request_id": request_id},
        "results": {
            "channels": [
                {
                    "detected_language": language,
                    "language_confidence": 0.99,
                    "alternatives": [
                        {
                            "transcript": text,
                            "words": words,
                            "paragraphs": {"transcript": text},
                        }
                    ],
                }
            ],
            "utterances": [
                {
                    "start": 0.0,
                    "end": 1.2,
                    "speaker": speaker,
                    "transcript": text,
                    "words": words,
                }
            ],
        },
    }


def _load_multilingual_benchmark_module():
    path = Path(__file__).resolve().parent / "test_live_transcribe_multilingual_matrix.py"
    spec = importlib.util.spec_from_file_location("live_transcribe_multilingual_matrix", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_prepare_transcription_audio_default_uses_normalized_wav(tmp_path):
    from easy_ai_clients.audio import PreparedTranscriptionAudio, prepare_transcription_audio

    prepared = prepare_transcription_audio(str(_write_audio_fixture(tmp_path)))

    assert isinstance(prepared, PreparedTranscriptionAudio)
    assert prepared.audio is not None
    assert prepared.audio.frame_rate == 16000
    assert prepared.audio.channels == 1
    assert prepared.audio.sample_width == 2
    assert prepared.audio_bytes.startswith(b"RIFF")
    assert prepared.content_type == "audio/wav"
    assert prepared.file_name == "audio.wav"
    assert prepared.audio_duration_seconds > 0
    assert prepared.upload_format == "wav"
    assert prepared.normalized is True
    assert prepared.source_format == "wav"


def test_build_request_audio_prepared_returns_bytes_without_reexport(monkeypatch):
    from easy_ai_clients.audio._transcribe import pre_processing

    prepared = _prepared_stub(
        audio_bytes=b"already-exported",
        content_type="audio/ogg",
        file_name="audio.ogg",
        upload_format="ogg",
        source_format="mp3",
        codec="libopus",
        bitrate="24k",
    )

    def fail_export(*args, **kwargs):
        raise AssertionError("prepared audio should not be exported again")

    monkeypatch.setattr(pre_processing, "export_segment", fail_export)

    request_audio = pre_processing.build_request_audio(prepared)

    assert request_audio["audio_bytes"] == b"already-exported"
    assert request_audio["content_type"] == "audio/ogg"
    assert request_audio["file_name"] == "audio.ogg"
    assert request_audio["upload_format"] == "ogg"
    assert request_audio["codec"] == "libopus"
    assert request_audio["bitrate"] == "24k"


def test_load_audio_prepared_uses_embedded_segment():
    from easy_ai_clients.audio._transcribe import pre_processing

    if pre_processing.AudioSegment is None:
        pytest.skip("pydub is required for prepared audio segment tests")

    segment = (
        pre_processing.AudioSegment.silent(duration=1000, frame_rate=16000)
        .set_channels(1)
        .set_sample_width(2)
    )
    prepared = _prepared_stub(audio=segment)

    assert pre_processing.load_audio(prepared) is segment


def test_prepare_transcription_audio_rejects_invalid_format_and_missing_file(tmp_path):
    from easy_ai_clients.audio import prepare_transcription_audio

    with pytest.raises(ValueError, match="Unsupported transcription upload_format"):
        prepare_transcription_audio(str(_write_audio_fixture(tmp_path)), upload_format="zip")

    with pytest.raises(FileNotFoundError):
        prepare_transcription_audio("missing-audio-file.mp3")


def test_prepare_transcription_audio_wraps_export_failures():
    from easy_ai_clients.audio._transcribe import pre_processing

    if pre_processing.AudioSegment is None:
        pytest.skip("pydub is required for export failure tests")

    segment = pre_processing.AudioSegment.silent(duration=250, frame_rate=16000)

    with pytest.raises(ValueError, match="Could not export transcription audio"):
        pre_processing.prepare_transcription_audio(
            segment,
            upload_format="ogg",
            codec="not-a-real-codec",
        )


def test_audio_transcribe_prepared_reaches_provider_without_repreparing(monkeypatch):
    from easy_ai_clients import audio
    from easy_ai_clients.audio._transcribe._apis import deepgram as provider

    prepared = _prepared_stub()
    captured = {}

    def fake_prepare(*args, **kwargs):
        raise AssertionError("prepared audio should not be prepared again")

    def fake_transcribe(audio_input, model="nova-2", **kwargs):
        captured["audio_input"] = audio_input
        captured["model"] = model
        captured["kwargs"] = kwargs
        return {"text": "ok"}

    monkeypatch.setattr(audio, "prepare_transcription_audio", fake_prepare)
    monkeypatch.setattr(provider, "transcribe", fake_transcribe)

    result = audio.transcribe(prepared, api="deepgram", model="nova-3", language="pt")

    assert result["text"] == "ok"
    assert captured["audio_input"] is prepared
    assert captured["model"] == "nova-3"
    assert captured["kwargs"] == {"language": "pt"}


def test_audio_transcribe_audio_options_are_dispatcher_only(monkeypatch):
    from easy_ai_clients import audio
    from easy_ai_clients.audio._transcribe._apis import fireworks as provider

    prepared = _prepared_stub(
        audio_bytes=b"opus",
        content_type="audio/ogg",
        file_name="audio.ogg",
        upload_format="ogg",
        source_format="mp3",
        codec="libopus",
        bitrate="24k",
    )
    captured = {}

    def fake_prepare(audio_input, **kwargs):
        captured["prepare_audio_input"] = audio_input
        captured["prepare_kwargs"] = kwargs
        return prepared

    def fake_transcribe(audio_input, model="whisper-v3-turbo", **kwargs):
        captured["provider_audio_input"] = audio_input
        captured["provider_kwargs"] = kwargs
        return {"text": "ok"}

    monkeypatch.setattr(audio, "prepare_transcription_audio", fake_prepare)
    monkeypatch.setattr(provider, "transcribe", fake_transcribe)

    result = audio.transcribe(
        "audio.mp3",
        api="fireworks",
        model="whisper-v3",
        audio_upload_format="ogg",
        audio_upload_codec="libopus",
        audio_upload_bitrate="24k",
        preprocessing="none",
    )

    assert result["text"] == "ok"
    assert captured["prepare_audio_input"] == "audio.mp3"
    assert captured["prepare_kwargs"] == {
        "normalize": True,
        "upload_format": "ogg",
        "codec": "libopus",
        "bitrate": "24k",
    }
    assert captured["provider_audio_input"] is prepared
    assert captured["provider_kwargs"] == {"preprocessing": "none"}


def test_deepgram_prepared_single_upload_uses_prepared_bytes(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    prepared = _prepared_stub(
        audio_bytes=b"prepared-ogg",
        content_type="audio/ogg",
        file_name="audio.ogg",
        upload_format="ogg",
        source_format="mp3",
        codec="libopus",
        bitrate="24k",
    )
    calls = []

    def fake_post_audio(session, audio_bytes, content_type, request_params, api_key):
        calls.append(
            {
                "audio_bytes": audio_bytes,
                "content_type": content_type,
                "request_params": request_params,
                "api_key": api_key,
            }
        )
        return _deepgram_payload(language="pt")

    def fail_prepare(*args, **kwargs):
        raise AssertionError("prepared audio should not be prepared again")

    monkeypatch.setattr(deepgram, "_get_api_key", lambda: "key")
    monkeypatch.setattr(deepgram, "_lookup_total_exact_cost", lambda request_ids: (None, "no usage"))
    monkeypatch.setattr(deepgram, "_post_audio", fake_post_audio)
    monkeypatch.setattr(deepgram, "prepare_transcription_audio", fail_prepare)

    result = deepgram.transcribe(prepared, model="nova-3", language_mkd=False)

    assert len(calls) == 1
    assert result["text"] == "hello world"
    assert calls[0]["audio_bytes"] == b"prepared-ogg"
    assert calls[0]["content_type"] == "audio/ogg"
    assert calls[0]["request_params"]["model"] == "nova-3"
    assert result["request_id"] == ["dg-1"]
    assert result["words"]
    assert result["segments"]
    assert result["speaker_count"] == 1
    assert result["cost_source"] == "official_pricing_table"


def test_deepgram_diarize_model_omits_default_diarize():
    from easy_ai_clients.audio._transcribe._apis import deepgram

    params = deepgram._normalize_request_params(  # noqa: SLF001
        "nova-3-general",
        extra_request_params={"diarize_model": "latest"},
    )

    assert params["diarize_model"] == "latest"
    assert "diarize" not in params


def test_deepgram_default_still_enables_diarize():
    from easy_ai_clients.audio._transcribe._apis import deepgram

    params = deepgram._normalize_request_params(  # noqa: SLF001
        "nova-3-general",
        extra_request_params={},
    )

    assert params["diarize"] == "true"


def test_deepgram_rejects_explicit_diarize_and_diarize_model_conflict():
    from easy_ai_clients.audio._transcribe._apis import deepgram

    with pytest.raises(ValueError, match="does not allow 'diarize' together with 'diarize_model'"):
        deepgram._normalize_request_params(  # noqa: SLF001
            "nova-3-general",
            extra_request_params={"diarize": True, "diarize_model": "latest"},
        )

    with pytest.raises(ValueError, match="does not allow 'diarize' together with 'diarize_model'"):
        deepgram.transcribe(_prepared_stub(), diarize=True, diarize_model="latest")


def test_deepgram_dispatcher_diarize_model_uses_effective_request_params(monkeypatch):
    from easy_ai_clients import audio
    from easy_ai_clients.audio._transcribe._apis import deepgram

    prepared = _prepared_stub(audio_bytes=b"dispatcher-wav", duration=2.0)
    calls = []

    monkeypatch.setattr(audio, "prepare_transcription_audio", lambda audio_input, **kwargs: prepared)
    monkeypatch.setattr(deepgram, "_get_api_key", lambda: "key")
    monkeypatch.setattr(deepgram, "_lookup_total_exact_cost", lambda request_ids: (None, "no usage"))

    def fake_post_audio(session, audio_bytes, content_type, request_params, api_key):
        calls.append(
            {
                "audio_bytes": audio_bytes,
                "content_type": content_type,
                "request_params": request_params,
            }
        )
        return _deepgram_payload()

    monkeypatch.setattr(deepgram, "_post_audio", fake_post_audio)

    result = audio.transcribe(
        "audio.mp3",
        api="deepgram",
        model="nova-3-general",
        diarize_model="latest",
        filler_words=False,
    )

    assert len(calls) == 1
    assert calls[0]["request_params"]["diarize_model"] == "latest"
    assert "diarize" not in calls[0]["request_params"]
    assert "filler_words" not in calls[0]["request_params"]
    assert result["provider_metadata"]["request_parameters"]["diarize_model"] == "latest"
    assert "diarize" not in result["provider_metadata"]["request_parameters"]


def test_deepgram_dispatcher_sends_single_post_for_one_input(monkeypatch):
    from easy_ai_clients import audio
    from easy_ai_clients.audio._transcribe._apis import deepgram

    prepared = _prepared_stub(audio_bytes=b"dispatcher-wav", duration=2.0)
    calls = []

    monkeypatch.setattr(audio, "prepare_transcription_audio", lambda audio_input, **kwargs: prepared)
    monkeypatch.setattr(deepgram, "_get_api_key", lambda: "key")
    monkeypatch.setattr(deepgram, "_lookup_total_exact_cost", lambda request_ids: (0.001234, None))

    def fake_post_audio(session, audio_bytes, content_type, request_params, api_key):
        calls.append(
            {
                "audio_bytes": audio_bytes,
                "content_type": content_type,
                "request_params": request_params,
            }
        )
        return _deepgram_payload()

    monkeypatch.setattr(deepgram, "_post_audio", fake_post_audio)

    result = audio.transcribe(
        "audio.mp3",
        api="deepgram",
        model="nova-3",
        language="en",
        smart_format=False,
        tag=["unit"],
    )

    assert len(calls) == 1
    assert calls[0]["audio_bytes"] == b"dispatcher-wav"
    assert calls[0]["request_params"]["model"] == "nova-3"
    assert calls[0]["request_params"]["language"] == "en"
    assert "detect_language" not in calls[0]["request_params"]
    assert calls[0]["request_params"]["smart_format"] == "false"
    assert calls[0]["request_params"]["tag"] == ["unit"]
    assert result["provider"] == "deepgram"
    assert result["model"] == "nova-3"
    assert result["text"] == "hello world"
    assert result["word_count"] == 2
    assert result["character_count"] == 10
    assert result["speaker_count"] == 1
    assert result["request_id"] == ["dg-1"]
    assert result["cost_usd"] == pytest.approx(0.001234)
    assert result["cost_source"] == "usage_lookup"
    assert result["cost_is_estimated"] is False
    assert result["cost_lookup_error"] is None


def test_deepgram_long_prepared_audio_still_sends_one_post(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    prepared = _prepared_stub(audio_bytes=b"long-audio", duration=7200.0)
    calls = []

    monkeypatch.setattr(deepgram, "_get_api_key", lambda: "key")
    monkeypatch.setattr(deepgram, "_lookup_total_exact_cost", lambda request_ids: (None, "no usage"))

    def fake_post_audio(session, audio_bytes, content_type, request_params, api_key):
        calls.append(request_params)
        return _deepgram_payload(duration=7200.0)

    monkeypatch.setattr(deepgram, "_post_audio", fake_post_audio)

    result = deepgram.transcribe(prepared, model="nova-3", language_mkd=False)

    assert len(calls) == 1
    assert calls[0]["detect_language"] == "true"
    assert result["duration"] == 7_200_000
    assert result["cost_source"] == "official_pricing_table"


def test_deepgram_post_audio_does_not_retry_failed_upload():
    import requests

    from easy_ai_clients.audio._transcribe._apis import deepgram

    class FailedResponse:
        status_code = 429
        text = "rate limited"

        def json(self):
            return {"err_msg": "rate limited"}

        def raise_for_status(self):
            raise requests.HTTPError(response=self)

    class FakeSession:
        def __init__(self):
            self.post_calls = 0

        def post(self, *args, **kwargs):
            self.post_calls += 1
            return FailedResponse()

    session = FakeSession()

    with pytest.raises(RuntimeError, match="Deepgram audio upload failed with status 429"):
        deepgram._post_audio(session, b"audio", "audio/wav", {"model": "nova-3"}, "key")

    assert session.post_calls == 1


def test_deepgram_fallback_model_sends_one_post_per_attempt(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    prepared = _prepared_stub(audio_bytes=b"fallback-audio", duration=3.0)
    attempted_models = []

    monkeypatch.setattr(deepgram, "_get_api_key", lambda: "key")
    monkeypatch.setattr(deepgram, "_lookup_total_exact_cost", lambda request_ids: (None, "no usage"))

    def fake_post_audio(session, audio_bytes, content_type, request_params, api_key):
        attempted_models.append(request_params["model"])
        if request_params["model"] == "nova-2":
            raise RuntimeError("primary failed")
        return _deepgram_payload(request_id="dg-fallback", text="fallback text")

    monkeypatch.setattr(deepgram, "_post_audio", fake_post_audio)

    result = deepgram.transcribe(
        prepared,
        model="nova-2",
        fallback_model="nova-3",
        language_mkd=False,
    )

    assert attempted_models == ["nova-2", "nova-3"]
    assert result["request_id"] == ["dg-fallback"]
    assert result["model"] == "nova-3"
    assert result["provider_metadata"]["requested_model"] == "nova-2"
    assert result["provider_metadata"]["actual_model"] == "nova-3"
    assert result["provider_metadata"]["fallback_model"] == "nova-3"


def test_elevenlabs_uses_other_file_format_for_encoded_prepared_upload(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import elevenlabs

    captured = {}

    monkeypatch.setattr(
        elevenlabs,
        "build_request_audio",
        lambda audio_input: {
            "file_name": "audio.mp3",
            "audio_bytes": b"mp3",
            "content_type": "audio/mpeg",
            "audio_duration_seconds": 1.0,
            "upload_format": "mp3",
            "normalized": True,
        },
    )
    monkeypatch.setattr(elevenlabs, "get_required_api_key", lambda env_var: "key")

    def fake_request(*args, **kwargs):
        captured["data"] = kwargs["data"]
        captured["files"] = kwargs["files"]
        return FakeResponse(
            {
                "text": "ola",
                "words": [],
                "audio_duration_secs": 1.0,
                "language_code": "por",
            }
        )

    monkeypatch.setattr(elevenlabs, "request_with_retries", fake_request)

    result = elevenlabs.transcribe("audio.mp3", model="scribe_v2", language_mkd=False)

    assert result["text"] == "ola"
    assert ("file_format", "other") in captured["data"]
    assert captured["files"]["file"] == ("audio.mp3", b"mp3", "audio/mpeg")


def test_falai_data_url_uses_prepared_content_type(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import falai

    captured = {}

    monkeypatch.setattr(
        falai,
        "build_request_audio",
        lambda audio_input: {
            "file_name": "audio.ogg",
            "audio_bytes": b"ogg-bytes",
            "content_type": "audio/ogg",
            "audio_duration_seconds": 1.0,
            "upload_format": "ogg",
            "normalized": True,
        },
    )
    monkeypatch.setattr(falai, "get_required_api_key", lambda env_var: "key")

    def fake_request(method, url, **kwargs):
        if method == "POST":
            captured["json_body"] = kwargs["json_body"]
            return FakeResponse(
                {
                    "status_url": "https://fal.example/status",
                    "response_url": "https://fal.example/response",
                    "request_id": "fal-1",
                }
            )
        if url == "https://fal.example/status":
            return FakeResponse({"status": "COMPLETED"})
        if url == "https://fal.example/response":
            return FakeResponse(
                {"text": "ola", "words": [], "language_code": "por"},
                headers={"X-Fal-Billable-Units": "1"},
            )
        return FakeResponse({"prices": [{"unit_price": 0.01, "unit": "minutes"}]})

    monkeypatch.setattr(falai, "request_with_retries", fake_request)

    result = falai.transcribe("audio.mp3", language_mkd=False)

    assert result["text"] == "ola"
    assert captured["json_body"]["audio_url"].startswith("data:audio/ogg;base64,")


def test_multilingual_benchmark_doc_parser_reads_blocked_rows(tmp_path):
    benchmark = _load_multilingual_benchmark_module()
    doc_path = tmp_path / "benchmark.md"
    doc_path.write_text(
        """# Live Multilingual Transcription Benchmark

## Detailed Results

| Provider | Model | Audio | Mode | Lang param/code | Returned lang | Elapsed (s) | Duration (s) | WER | Word acc | CER | Char sim | Cost USD | Cost status | Request ID | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fireworks | whisper-v3-turbo | Bengali | explicit | language: bn |  | 0.123 | 46.366 |  |  |  |  |  | account_or_credit_blocked |  | account_or_credit_blocked |

## Returned Transcripts And Errors

<details><summary>1. fireworks / whisper-v3-turbo / Bengali / explicit / account_or_credit_blocked</summary>

| Field | Value |
| --- | --- |
| language parameter | language |
| language code | bn |
| returned language |  |
| elapsed seconds | 0.123 |
| request_id |  |
| cost_usd |  |
| cost_source |  |
| cost_is_estimated |  |
| cost_lookup_error |  |
| cost_update_attempted | False |
| error_type | RuntimeError |
| error_message | HTTP 401 during API request. |

**Transcript**

<pre>

</pre>

</details>

## Rerun Instructions
""",
        encoding="utf-8",
    )

    rows = benchmark._parse_existing_benchmark_doc(doc_path)

    assert len(rows) == 1
    assert rows[0]["provider"] == "fireworks"
    assert rows[0]["model"] == "whisper-v3-turbo"
    assert rows[0]["language_code"] == "bn"
    assert rows[0]["status"] == "account_or_credit_blocked"


def test_transcription_bundle_preserves_unknown_cost_metadata():
    from easy_ai_clients.audio._transcribe.post_processing import (
        _build_transcription_bundle,
        build_raw_transcription_payload,
    )

    raw_payload = build_raw_transcription_payload(
        provider="unit",
        model="demo",
        audio_duration_seconds=1.0,
        language="auto",
        text="hello",
    )
    bundle = _build_transcription_bundle(
        raw_payload,
        language_mkd=False,
        cost_usd=None,
        cost_source="unavailable",
        cost_is_estimated=False,
        cost_lookup_error=None,
    )

    assert bundle["cost_usd"] is None
    assert bundle["cost_source"] == "unavailable"
    assert bundle["cost_is_estimated"] is False
    assert bundle["cost_lookup_error"] is None


def test_cost_lookup_error_sanitizes_known_secrets(monkeypatch):
    from easy_ai_clients.audio._transcribe.post_processing import _sanitize_cost_lookup_error

    monkeypatch.setenv("DEEPGRAM_API_KEY", "secret-token-123")

    message = _sanitize_cost_lookup_error(
        "Authorization: Token secret-token-123 api_key=secret-token-123"
    )

    assert "secret-token-123" not in message
    assert "[redacted]" in message


def test_removed_deepgram_models_are_forward_compatible():
    from easy_ai_clients.audio._transcribe._apis import deepgram

    for model in ("base", "base-general", "whisper-tiny", "whisper-base"):
        assert deepgram._validate_model(model) is None  # noqa: SLF001


def test_deepgram_no_hidden_fallback_by_default(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    prepared = _prepared_stub(audio_bytes=b"primary-audio", duration=1.0)
    attempted_models = []

    monkeypatch.setattr(deepgram, "_get_api_key", lambda: "key")

    def fake_post_audio(session, audio_bytes, content_type, request_params, api_key):
        attempted_models.append(request_params["model"])
        raise RuntimeError("primary failed")

    monkeypatch.setattr(deepgram, "_post_audio", fake_post_audio)

    with pytest.raises(RuntimeError, match="Transcription with model 'nova-2' failed"):
        deepgram.transcribe(prepared, model="nova-2")

    assert attempted_models == ["nova-2"]


def test_deepgram_exact_cost_lookup_success_metadata(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    monkeypatch.setattr(deepgram, "_lookup_total_exact_cost", lambda request_ids: (0.012345, None))

    metadata = deepgram._resolve_deepgram_cost_metadata(
        request_ids=["req-1"],
        model_name="nova-3",
        audio_duration_seconds=60,
        diarize=True,
    )

    assert metadata == {
        "cost_usd": 0.012345,
        "cost_source": "usage_lookup",
        "cost_is_estimated": False,
        "cost_lookup_error": None,
    }


def test_deepgram_lookup_failure_uses_nova3_estimate(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    monkeypatch.setattr(
        deepgram,
        "_lookup_total_exact_cost",
        lambda request_ids: (None, "usage:read scope is required"),
    )

    metadata = deepgram._resolve_deepgram_cost_metadata(
        request_ids=["req-1"],
        model_name="nova-3",
        audio_duration_seconds=60,
        diarize=True,
    )

    assert metadata["cost_usd"] == pytest.approx(0.0112)
    assert metadata["cost_source"] == "official_pricing_table"
    assert metadata["cost_is_estimated"] is True
    assert "usage:read" in metadata["cost_lookup_error"]


def test_deepgram_lookup_failure_is_unknown_for_non_nova3(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    monkeypatch.setattr(
        deepgram,
        "_lookup_total_exact_cost",
        lambda request_ids: (None, "usage:read scope is required"),
    )

    metadata = deepgram._resolve_deepgram_cost_metadata(
        request_ids=["req-1"],
        model_name="nova-2",
        audio_duration_seconds=27,
        diarize=True,
    )

    assert metadata["cost_usd"] == 0.0
    assert metadata["cost_source"] == "unavailable"
    assert metadata["cost_is_estimated"] is False
    assert "usage:read" in metadata["cost_lookup_error"]


def test_deepgram_update_cost_sanitizes_lookup_error(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import deepgram

    monkeypatch.setenv("DEEPGRAM_API_KEY", "secret-token-123")
    monkeypatch.setattr(
        deepgram,
        "_resolve_deepgram_cost_metadata",
        lambda **kwargs: {
            "cost_usd": None,
            "cost_source": "unavailable",
            "cost_is_estimated": False,
            "cost_lookup_error": "usage lookup failed with token secret-token-123",
        },
    )

    result = deepgram.update_cost(
        {
            "request_id": "req-1",
            "model": "nova-2",
            "duration": 1000,
            "provider_metadata": {"request_parameters": {"diarize": True}},
            "text": "hello",
        }
    )

    assert result["cost_usd"] is None
    assert result["cost_source"] == "unavailable"
    assert "secret-token-123" not in result["cost_lookup_error"]


def test_deepgram_exact_cost_parsing_from_lookup_payload():
    from easy_ai_clients.audio._transcribe._apis.deepgram import _extract_exact_cost_from_lookup

    payload = {"request": {"response": {"details": {"cost": {"usd": "0.123456"}}}}}

    assert float(_extract_exact_cost_from_lookup(payload)) == pytest.approx(0.123456)


def test_fireworks_cost_has_no_diarization_multiplier(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import fireworks

    monkeypatch.setattr(
        fireworks,
        "build_request_audio",
        lambda audio_input: {
            "file_name": "audio.wav",
            "audio_bytes": b"wav",
            "content_type": "audio/wav",
            "audio_duration_seconds": 60.0,
        },
    )
    monkeypatch.setattr(fireworks, "get_required_api_key", lambda env_var: "key")
    monkeypatch.setattr(
        fireworks,
        "request_with_retries",
        lambda *args, **kwargs: FakeResponse(
            {
                "duration": 60.0,
                "language": "pt",
                "text": "hello",
                "words": [{"word": "hello", "start": 0, "end": 1}],
                "segments": [{"id": 0, "start": 0, "end": 1, "text": "hello"}],
                "request_id": "fw-1",
            }
        ),
    )

    result = fireworks.transcribe("audio.mp3", model="whisper-v3", diarize=True, language_mkd=False)

    assert result["cost_usd"] == pytest.approx(0.0015)
    assert result["cost_source"] == "official_pricing_table"
    assert result["cost_is_estimated"] is True


def test_speechmatics_prices_and_auto_language(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import speechmatics

    assert speechmatics._compute_speechmatics_cost(
        3600,
        model="standard",
        config_payload={"type": "transcription"},
    ) == pytest.approx(0.45)
    assert speechmatics._compute_speechmatics_cost(
        3600,
        model="enhanced",
        config_payload={"type": "transcription"},
    ) == pytest.approx(0.75)

    captured = {}

    def fake_request(method, url, **kwargs):
        if method == "POST":
            captured["config"] = json.loads(kwargs["files"]["config"][1])
            return FakeResponse({"id": "job-1"})
        if url.endswith("/jobs/job-1/transcript"):
            return FakeResponse(
                {
                    "job": {"duration": 10.0},
                    "metadata": {"transcription_config": {"language": "auto"}},
                    "results": [],
                }
            )
        return FakeResponse({"job": {"status": "done"}})

    monkeypatch.setattr(
        speechmatics,
        "build_request_audio",
        lambda audio_input: {
            "file_name": "audio.wav",
            "audio_bytes": b"wav",
            "content_type": "audio/wav",
            "audio_duration_seconds": 10.0,
        },
    )
    monkeypatch.setattr(speechmatics, "get_required_api_key", lambda env_var: "key")
    monkeypatch.setattr(speechmatics, "request_with_retries", fake_request)

    speechmatics.transcribe("audio.mp3", language_mkd=False)

    assert captured["config"]["transcription_config"]["language"] == "auto"


def test_elevenlabs_official_addon_pricing_only():
    from easy_ai_clients.audio._transcribe._apis import elevenlabs

    assert elevenlabs._compute_elevenlabs_cost(
        3600,
        model="scribe_v2",
        entity_detection=["person"],
        keyterms=["Bento"],
    ) == pytest.approx(0.34)
    assert elevenlabs._compute_elevenlabs_cost(
        3600,
        model="scribe_v2",
        entity_detection=None,
        keyterms=None,
    ) == pytest.approx(0.22)


def test_falai_cost_uses_billable_units_and_pricing_api_fallback(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import falai

    monkeypatch.setattr(
        falai,
        "request_with_retries",
        lambda *args, **kwargs: FakeResponse(
            {"prices": [{"unit_price": 0.008, "unit": "minutes", "currency": "USD"}]}
        ),
    )

    with_header = falai._resolve_fal_cost_metadata(
        "key",
        "fal-ai/elevenlabs/speech-to-text/scribe-v2",
        27,
        "2",
    )
    without_header = falai._resolve_fal_cost_metadata(
        "key",
        "fal-ai/elevenlabs/speech-to-text/scribe-v2",
        60,
        None,
    )

    assert with_header["cost_usd"] == pytest.approx(0.016)
    assert with_header["cost_source"] == "pricing_api_billable_units"
    assert without_header["cost_usd"] == pytest.approx(0.008)
    assert without_header["cost_source"] == "pricing_api"


def test_falai_invalid_pricing_value_is_unavailable(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import falai

    monkeypatch.setattr(
        falai,
        "request_with_retries",
        lambda *args, **kwargs: FakeResponse(
            {"prices": [{"unit_price": "not-a-number", "unit": "minutes", "currency": "USD"}]}
        ),
    )

    metadata = falai._resolve_fal_cost_metadata(
        "key",
        "fal-ai/elevenlabs/speech-to-text/scribe-v2",
        60,
        None,
    )

    assert metadata["cost_usd"] == 0.0
    assert metadata["cost_source"] == "unavailable"
    assert metadata["cost_is_estimated"] is False
    assert "invalid unit_price" in metadata["cost_lookup_error"]


def test_removed_together_models_use_unknown_cost_metadata(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import together

    monkeypatch.setattr(together, "request_with_retries", lambda *args, **kwargs: FakeResponse({"data": []}))

    for model in ("deepgram/flux", "deepgram/nova-3-en", "deepgram/nova-3-multi"):
        metadata = together._resolve_together_cost_metadata("key", model, 60)  # noqa: SLF001
        assert metadata["cost_usd"] == 0.0
        assert metadata["cost_source"] == "unavailable"
        assert "No documented pricing metadata" in metadata["cost_lookup_error"]


def test_together_cost_prefers_pricing_api(monkeypatch):
    from easy_ai_clients.audio._transcribe._apis import together

    monkeypatch.setattr(
        together,
        "request_with_retries",
        lambda *args, **kwargs: FakeResponse(
            {
                "data": [
                    {
                        "id": "openai/whisper-large-v3",
                        "pricing": {"transcribe": {"price_per_minute": "0.0015"}},
                    }
                ]
            }
        ),
    )

    metadata = together._resolve_together_cost_metadata(
        "key",
        "openai/whisper-large-v3",
        60,
    )

    assert metadata["cost_usd"] == pytest.approx(0.0015)
    assert metadata["cost_source"] == "pricing_api"
    assert metadata["cost_is_estimated"] is True
