"""Gated live transcription validation.

Run with `EASY_AI_CLIENTS_LIVE_TRANSCRIBE=1 pytest tests/test_live_transcribe.py -s`.
This module intentionally leaves no result artifacts in the repository.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
AUDIO_FIXTURE = ROOT / "audio.mp3"
TRANSCRIPT_FIXTURE = ROOT / "audio.txt"

PROVIDER_ENV = {
    "deepgram": "DEEPGRAM_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "falai": "FAL_KEY",
    "fireworks": "FIREWORKS_API_KEY",
    "speechmatics": "SPEECHMATICS_API_KEY",
    "together": "TOGETHER_API_KEY",
}
VALID_COST_SOURCES = {
    "provider_response",
    "usage_lookup",
    "pricing_api",
    "pricing_api_billable_units",
    "official_pricing_table",
    "unavailable",
}
REQUIRED_COST_KEYS = {
    "cost_usd",
    "cost_source",
    "cost_is_estimated",
    "cost_lookup_error",
}

LIVE_MODELS = [
    ("deepgram", "nova-3", {}),
    ("deepgram", "nova-3-general", {}),
    ("deepgram", "nova-3-medical", {}),
    ("deepgram", "nova-2", {}),
    ("deepgram", "nova-2-general", {}),
    ("deepgram", "nova-2-meeting", {}),
    ("deepgram", "nova-2-phonecall", {}),
    ("deepgram", "nova-2-voicemail", {}),
    ("deepgram", "nova-2-finance", {}),
    ("deepgram", "nova-2-conversationalai", {}),
    ("deepgram", "nova-2-video", {}),
    ("deepgram", "nova-2-medical", {}),
    ("deepgram", "nova-2-drivethru", {}),
    ("deepgram", "nova-2-automotive", {}),
    ("deepgram", "nova-2-atc", {}),
    ("deepgram", "nova", {}),
    ("deepgram", "nova-general", {}),
    ("deepgram", "nova-phonecall", {}),
    ("deepgram", "enhanced", {}),
    ("deepgram", "enhanced-general", {}),
    ("deepgram", "enhanced-meeting", {}),
    ("deepgram", "enhanced-phonecall", {}),
    ("deepgram", "enhanced-finance", {}),
    ("deepgram", "base-meeting", {}),
    ("deepgram", "base-phonecall", {}),
    ("deepgram", "base-voicemail", {}),
    ("deepgram", "base-finance", {}),
    ("deepgram", "base-conversationalai", {}),
    ("deepgram", "base-video", {}),
    ("deepgram", "whisper", {}),
    ("deepgram", "whisper-small", {}),
    ("deepgram", "whisper-medium", {}),
    ("deepgram", "whisper-large", {}),
    ("elevenlabs", "scribe_v1", {}),
    ("elevenlabs", "scribe_v2", {}),
    ("falai", "fal-ai/elevenlabs/speech-to-text", {}),
    ("falai", "fal-ai/elevenlabs/speech-to-text/scribe-v2", {}),
    ("fireworks", "whisper-v3", {}),
    ("fireworks", "whisper-v3-turbo", {}),
    ("speechmatics", "standard", {}),
    ("speechmatics", "enhanced", {}),
    ("together", "openai/whisper-large-v3", {}),
    ("together", "nvidia/parakeet-tdt-0.6b-v3", {}),
]


def _words(text):
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def _levenshtein_distance(left, right):
    previous = list(range(len(right) + 1))
    for left_index, left_item in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_item in enumerate(right, start=1):
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + (left_item != right_item),
                )
            )
        previous = current
    return previous[-1]


def _word_metrics(reference, observed):
    reference_words = _words(reference)
    if not reference_words:
        return 1.0, 0.0
    distance = _levenshtein_distance(reference_words, _words(observed))
    wer = distance / len(reference_words)
    return max(0.0, 1.0 - wer), wer


def _character_similarity(reference, observed):
    reference_text = re.sub(r"\s+", "", str(reference or "").lower())
    observed_text = re.sub(r"\s+", "", str(observed or "").lower())
    if not reference_text:
        return 1.0 if not observed_text else 0.0
    distance = _levenshtein_distance(list(reference_text), list(observed_text))
    return max(0.0, 1.0 - (distance / len(reference_text)))


def _short_error(error):
    return " ".join(str(error).split())[:500]


@pytest.mark.parametrize(("api", "model", "kwargs"), LIVE_MODELS)
def test_live_transcribe_model(api, model, kwargs):
    if os.getenv("EASY_AI_CLIENTS_LIVE_TRANSCRIBE") != "1":
        pytest.skip("live transcription validation is gated by EASY_AI_CLIENTS_LIVE_TRANSCRIBE=1")

    load_dotenv(ROOT / ".env", override=False)

    if not AUDIO_FIXTURE.exists() or not TRANSCRIPT_FIXTURE.exists():
        pytest.skip("live accuracy validation skipped because audio.mp3/audio.txt fixtures are missing")

    env_var = PROVIDER_ENV[api]
    if not os.getenv(env_var):
        pytest.skip(f"live transcription validation skipped for api='{api}' because {env_var} is missing")

    from easy_ai_clients import audio

    reference_text = TRANSCRIPT_FIXTURE.read_text(encoding="utf-8")
    started = time.perf_counter()
    try:
        result = audio.transcribe(str(AUDIO_FIXTURE), api=api, model=model, **kwargs)
    except Exception as error:
        elapsed = time.perf_counter() - started
        print(
            f"{api} | {model} | error | elapsed={elapsed:.3f}s | "
            f"error={_short_error(error)}"
        )
        raise

    elapsed = time.perf_counter() - started
    word_accuracy, wer = _word_metrics(reference_text, result.get("text"))
    char_similarity = _character_similarity(reference_text, result.get("text"))
    print(
        f"{api} | {model} | ok | elapsed={elapsed:.3f}s | "
        f"language={result.get('language')} | wer={wer:.3f} | "
        f"word_accuracy={word_accuracy:.3f} | char_similarity={char_similarity:.3f} | "
        f"cost_usd={result.get('cost_usd')} | "
        f"cost_source={result.get('cost_source')} | "
        f"cost_is_estimated={result.get('cost_is_estimated')} | "
        f"error={result.get('cost_lookup_error')}"
    )

    assert result.get("text")
    assert REQUIRED_COST_KEYS <= set(result)
    assert result["cost_source"] in VALID_COST_SOURCES
    assert isinstance(result["cost_is_estimated"], bool)
    if result["cost_source"] == "unavailable":
        assert result["cost_usd"] is None
        assert result["cost_is_estimated"] is False
    else:
        assert isinstance(result["cost_usd"], int | float)
    assert word_accuracy >= 0.80
