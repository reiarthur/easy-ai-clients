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


def _load_multilingual_benchmark_module():
    path = Path(__file__).resolve().parent / "test_live_transcribe_multilingual_matrix.py"
    spec = importlib.util.spec_from_file_location("live_transcribe_multilingual_matrix", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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

    class FakeAudio:
        def __len__(self):
            return 1000

    calls = []
    primary_error = RuntimeError("primary failed")

    def fake_transcribe_with_model(*args, **kwargs):
        calls.append(args[2])
        return None, ["req-1"], primary_error

    monkeypatch.setattr(deepgram, "load_audio", lambda audio_input: FakeAudio())
    monkeypatch.setattr(deepgram, "build_balanced_spans", lambda audio: [(0, 1000)])
    monkeypatch.setattr(deepgram, "_transcribe_with_model", fake_transcribe_with_model)

    with pytest.raises(RuntimeError, match="primary failed"):
        deepgram.transcribe("audio.mp3", model="nova-2")

    assert calls == ["nova-2"]


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
