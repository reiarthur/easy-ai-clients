"""Sequential multilingual live transcription benchmark.

Normal pytest runs skip this module. Paid provider calls run only when
`EASY_AI_CLIENTS_LIVE_TRANSCRIBE_MULTILINGUAL=1` is set, or when this file is
executed directly with the same environment flag.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import os
import re
import subprocess
import tarfile
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = ROOT / "tests" / "fixtures" / "transcribe_multilingual_audios.tar.xz"
DOC_PATH = ROOT / "docs" / "audio" / "transcribe" / "live_multilingual_benchmark.md"

LIVE_ENV_VAR = "EASY_AI_CLIENTS_LIVE_TRANSCRIBE_MULTILINGUAL"
FILTER_ENV_VARS = {
    "providers": "EASY_AI_CLIENTS_BENCHMARK_PROVIDERS",
    "models": "EASY_AI_CLIENTS_BENCHMARK_MODELS",
    "audios": "EASY_AI_CLIENTS_BENCHMARK_AUDIOS",
    "modes": "EASY_AI_CLIENTS_BENCHMARK_MODES",
}

PROVIDER_ENV = {
    "deepgram": "DEEPGRAM_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "falai": "FAL_KEY",
    "fireworks": "FIREWORKS_API_KEY",
    "speechmatics": "SPEECHMATICS_API_KEY",
    "together": "TOGETHER_API_KEY",
}

EXPECTED_FIXTURES = {
    "Arabic": "Arabic",
    "Bengali": "Bengali",
    "English": "English",
    "French": "French",
    "Hindi": "Hindi",
    "Mandarin": "Mandarin",
    "Portuguese-BR": "Portuguese (Brazil)",
    "Russian": "Russian",
    "Spanish": "Spanish",
    "Urdu": "Urdu",
}

EXPLICIT_LANGUAGE_CODES = {
    "deepgram": {
        "parameter": "language",
        "codes": {
            "Arabic": "ar",
            "Bengali": "bn",
            "English": "en",
            "French": "fr",
            "Hindi": "hi",
            "Mandarin": "zh",
            "Portuguese-BR": "pt-BR",
            "Russian": "ru",
            "Spanish": "es",
            "Urdu": "ur",
        },
    },
    "elevenlabs": {
        "parameter": "language_code",
        "codes": {
            "Arabic": "ara",
            "Bengali": "ben",
            "English": "eng",
            "French": "fra",
            "Hindi": "hin",
            "Mandarin": "zh",
            "Portuguese-BR": "por",
            "Russian": "rus",
            "Spanish": "spa",
            "Urdu": "urd",
        },
        "unsupported_models": {"scribe_v1"},
    },
    "falai": {
        "parameter": "language_code",
        "codes": {
            "Arabic": "ara",
            "Bengali": "ben",
            "English": "eng",
            "French": "fra",
            "Hindi": "hin",
            "Mandarin": "zh",
            "Portuguese-BR": "por",
            "Russian": "rus",
            "Spanish": "spa",
            "Urdu": "urd",
        },
    },
    "fireworks": {
        "parameter": "language",
        "codes": {
            "Arabic": "ar",
            "Bengali": "bn",
            "English": "en",
            "French": "fr",
            "Hindi": "hi",
            "Mandarin": "zh",
            "Portuguese-BR": "pt",
            "Russian": "ru",
            "Spanish": "es",
            "Urdu": "ur",
        },
    },
    "speechmatics": {
        "parameter": "language",
        "codes": {
            "Arabic": "ar",
            "Bengali": "bn",
            "English": "en",
            "French": "fr",
            "Hindi": "hi",
            "Mandarin": "cmn",
            "Portuguese-BR": "pt",
            "Russian": "ru",
            "Spanish": "es",
            "Urdu": "ur",
        },
    },
    "together": {
        "parameter": "language",
        "codes": {
            "Arabic": "ar",
            "Bengali": "bn",
            "English": "en",
            "French": "fr",
            "Hindi": "hi",
            "Mandarin": "zh",
            "Portuguese-BR": "pt",
            "Russian": "ru",
            "Spanish": "es",
            "Urdu": "ur",
        },
    },
}

DEEPGRAM_MODEL_LANGUAGE_CODES = {
    "nova-3": {
        "Arabic": "ar",
        "Bengali": "bn",
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt-BR",
        "Russian": "ru",
        "Spanish": "es",
        "Urdu": "ur",
    },
    "nova-3-general": {
        "Arabic": "ar",
        "Bengali": "bn",
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt-BR",
        "Russian": "ru",
        "Spanish": "es",
        "Urdu": "ur",
    },
    "nova-3-medical": {"English": "en"},
    "nova-2": {
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt-BR",
        "Russian": "ru",
        "Spanish": "es",
    },
    "nova-2-general": {
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt-BR",
        "Russian": "ru",
        "Spanish": "es",
    },
    "nova": {"English": "en", "Hindi": "hi-Latn", "Spanish": "es"},
    "nova-general": {"English": "en", "Hindi": "hi-Latn", "Spanish": "es"},
    "enhanced": {
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Portuguese-BR": "pt-BR",
        "Spanish": "es",
    },
    "enhanced-general": {
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Portuguese-BR": "pt-BR",
        "Spanish": "es",
    },
    "whisper": {
        "Arabic": "ar",
        "Bengali": "bn",
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt",
        "Russian": "ru",
        "Spanish": "es",
        "Urdu": "ur",
    },
    "whisper-small": {
        "Arabic": "ar",
        "Bengali": "bn",
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt",
        "Russian": "ru",
        "Spanish": "es",
        "Urdu": "ur",
    },
    "whisper-medium": {
        "Arabic": "ar",
        "Bengali": "bn",
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt",
        "Russian": "ru",
        "Spanish": "es",
        "Urdu": "ur",
    },
    "whisper-large": {
        "Arabic": "ar",
        "Bengali": "bn",
        "English": "en",
        "French": "fr",
        "Hindi": "hi",
        "Mandarin": "zh",
        "Portuguese-BR": "pt",
        "Russian": "ru",
        "Spanish": "es",
        "Urdu": "ur",
    },
}
for _deepgram_english_model in (
    "nova-2-meeting",
    "nova-2-phonecall",
    "nova-2-voicemail",
    "nova-2-finance",
    "nova-2-conversationalai",
    "nova-2-video",
    "nova-2-medical",
    "nova-2-drivethru",
    "nova-2-automotive",
    "nova-2-atc",
    "nova-phonecall",
    "enhanced-meeting",
    "enhanced-phonecall",
    "enhanced-finance",
    "base-meeting",
    "base-phonecall",
    "base-voicemail",
    "base-finance",
    "base-conversationalai",
    "base-video",
):
    DEEPGRAM_MODEL_LANGUAGE_CODES[_deepgram_english_model] = {"English": "en"}

AUTO_LANGUAGE_NOTES = {
    "deepgram": "No concrete language is passed; the adapter sends detect_language=true.",
    "elevenlabs": "language_code is omitted; ElevenLabs predicts the language.",
    "falai": "language_code is omitted; the upstream Fal.ai/ElevenLabs endpoint predicts the language.",
    "fireworks": "language is omitted; Fireworks/Whisper detects the language.",
    "speechmatics": "No concrete language is passed; the adapter default sends language='auto'.",
    "together": "No concrete language is passed; the adapter default sends language='auto'.",
}

COST_METHOD_NOTES = {
    "deepgram": (
        "Deepgram responses do not return final cost. The library tries Management/Usage "
        "lookup with request IDs and DEEPGRAM_PROJECT_ID when available. Nova-3 falls back "
        "to the official prerecorded per-minute table; older families remain unavailable "
        "when usage:read is blocked."
    ),
    "elevenlabs": (
        "ElevenLabs Scribe responses do not return invoice cost. The library estimates from "
        "the official Scribe hourly API pricing table and documented add-ons."
    ),
    "falai": (
        "Fal.ai uses the official Pricing API. X-Fal-Billable-Units is preferred when present; "
        "otherwise duration multiplied by the Pricing API unit price is used."
    ),
    "fireworks": (
        "Fireworks responses do not return cost. The library estimates from the official "
        "Whisper v3 per-audio-minute prices, billed by duration."
    ),
    "speechmatics": (
        "Speechmatics batch responses do not return invoice cost. The library estimates from "
        "the official batch standard/enhanced hourly prices and documented add-ons."
    ),
    "together": (
        "Together responses do not return cost. The library first reads authenticated /v1/models "
        "transcription pricing and falls back to documented per-minute serverless prices."
    ),
}

OFFICIAL_REFERENCE_LINKS = {
    "deepgram": [
        "https://developers.deepgram.com/docs/models-languages-overview/",
        "https://developers.deepgram.com/docs/using-logs-usage",
        "https://deepgram.com/pricing",
    ],
    "elevenlabs": [
        "https://elevenlabs.io/docs/api-reference/speech-to-text/convert",
        "https://elevenlabs.io/pricing/api",
    ],
    "falai": [
        "https://fal.ai/models/fal-ai/elevenlabs/speech-to-text/api",
        "https://fal.ai/models/fal-ai/elevenlabs/speech-to-text/scribe-v2/api",
        "https://fal.ai/docs/platform-apis/v1/models/pricing",
    ],
    "fireworks": [
        "https://docs.fireworks.ai/api-reference/audio-transcriptions",
        "https://fireworks.ai/models/fireworks/whisper-v3",
        "https://fireworks.ai/models/fireworks/whisper-v3-turbo",
    ],
    "speechmatics": [
        "https://docs.speechmatics.com/",
        "https://www.speechmatics.com/pricing",
    ],
    "together": [
        "https://docs.together.ai/reference/audio-transcriptions",
        "https://docs.together.ai/docs/serverless/models",
        "https://docs.together.ai/docs/billing-usage-limits",
    ],
}

INPUT_LIMIT_ROWS = [
    {
        "provider": "deepgram",
        "models": "All Deepgram models in this report",
        "endpoint": "Pre-recorded REST transcription, `POST /v1/listen`",
        "max_duration": (
            "No hard duration limit is stated; requests can time out after 10 minutes "
            "of processing for Nova/Base/Enhanced and 20 minutes for Whisper."
        ),
        "max_size": "2 GB file size.",
        "format_notes": (
            "Common supported formats include MP3, MP4, MP2, AAC, WAV, FLAC, PCM, "
            "M4A, Ogg, Opus, and WebM; Deepgram says it handles over 100 formats."
        ),
        "source": (
            "[Pre-recorded limits](https://developers.deepgram.com/docs/pre-recorded-audio) "
            "[Supported formats](https://developers.deepgram.com/docs/supported-audio-formats)"
        ),
        "status": "Official endpoint-level limit; processing timeout is not an upload-size limit.",
    },
    {
        "provider": "elevenlabs",
        "models": "scribe_v1, scribe_v2",
        "endpoint": "Speech-to-text API, `POST /v1/speech-to-text`, standard mode",
        "max_duration": "10 hours in standard mode (`use_multi_channel=false`).",
        "max_size": "3 GB file size.",
        "format_notes": (
            "Accepts audio and video; documented audio formats include AAC, AIFF, "
            "OGG, MP3, OPUS, WAV, FLAC, M4A, and WebM. Multichannel mode is separate "
            "and was not used in this benchmark."
        ),
        "source": (
            "[Speech-to-text overview FAQ](https://elevenlabs.io/docs/overview/capabilities/speech-to-text) "
            "[API reference](https://elevenlabs.io/docs/api-reference/speech-to-text/convert)"
        ),
        "status": "Official endpoint-level limit for the mode used here.",
    },
    {
        "provider": "falai",
        "models": "fal-ai/elevenlabs/speech-to-text; fal-ai/elevenlabs/speech-to-text/scribe-v2",
        "endpoint": "Fal.ai queued model API with `audio_url` input",
        "max_duration": "Not publicly specified in the official model pages reviewed.",
        "max_size": "Not publicly specified as a model input limit.",
        "format_notes": (
            "Model pages require an `audio_url`. Fal CDN/file docs describe upload "
            "storage separately and note that individual models may enforce their own "
            "size and format limits."
        ),
        "source": (
            "[Scribe v1 model page](https://fal.ai/models/fal-ai/elevenlabs/speech-to-text/api) "
            "[Scribe v2 model page](https://fal.ai/models/fal-ai/elevenlabs/speech-to-text/scribe-v2/api) "
            "[Fal CDN docs](https://fal.ai/docs/documentation/model-apis/fal-cdn)"
        ),
        "status": "Official model-specific duration/file-size limit not publicly specified.",
    },
    {
        "provider": "fireworks",
        "models": "whisper-v3, whisper-v3-turbo",
        "endpoint": (
            "Audio transcription API; `whisper-v3` uses `audio-prod.api.fireworks.ai`, "
            "`whisper-v3-turbo` uses `audio-turbo.api.fireworks.ai`."
        ),
        "max_duration": "No audio duration limit is documented.",
        "max_size": "1 GB maximum audio file size.",
        "format_notes": (
            "Common formats such as MP3, FLAC, and WAV are supported. Fireworks "
            "resamples to 16 kHz, downmixes to mono, and reformats before transcription."
        ),
        "source": "[Audio transcription API reference](https://docs.fireworks.ai/api-reference/audio-transcriptions)",
        "status": "Official endpoint-level limit; model-specific endpoints are documented.",
    },
    {
        "provider": "speechmatics",
        "models": "standard, enhanced",
        "endpoint": "Batch SaaS transcription job",
        "max_duration": "2 hours of audio.",
        "max_size": "1 GB file size.",
        "format_notes": "Supported file types: AAC, AMR, FLAC, M4A, MP3, MP4, MPEG, OGG, WAV.",
        "source": "[Batch SaaS introduction](https://legacy.docs.speechmatics.com/en/cloud/introduction/)",
        "status": "Official Batch SaaS limit in the official legacy Speechmatics docs.",
    },
    {
        "provider": "together",
        "models": "openai/whisper-large-v3, nvidia/parakeet-tdt-0.6b-v3",
        "endpoint": "Audio transcription API, `POST /audio/transcriptions`",
        "max_duration": "Not publicly specified in the official API and limits docs reviewed.",
        "max_size": "Not publicly specified in the official API and limits docs reviewed.",
        "format_notes": (
            "Supported formats listed by the API reference: .wav, .mp3, .m4a, .webm, "
            ".flac, .ogg, .opus, .aac. Together documents dynamic per-model rate "
            "limits and possible model-specific access restrictions."
        ),
        "source": (
            "[Audio transcription API reference](https://docs.together.ai/reference/audio-transcriptions) "
            "[Usage limits](https://docs.together.ai/docs/billing-usage-limits) "
            "[Serverless models](https://docs.together.ai/docs/serverless/models)"
        ),
        "status": "Official upload duration/file-size limit not publicly specified.",
    },
]

TRANSIENT_ERROR_MARKERS = (
    "timeout",
    "temporarily",
    "temporary",
    "rate limit",
    "too many requests",
    "429",
    "500",
    "502",
    "503",
    "504",
    "connection",
)
RERUNNABLE_STATUSES = {
    "account_or_credit_blocked",
    "account_or_credit_blocked_not_retried",
    "failed",
    "model_or_access_blocked",
    "model_or_access_blocked_not_retried",
    "not_run",
    "transient_failure",
}
ACCOUNT_BLOCK_MARKERS = (
    "insufficient",
    "credit",
    "quota",
    "billing",
    "payment",
    "balance",
    "unauthorized",
    "401",
    "forbidden",
    "403",
    "access denied",
    "does not have access",
)
MODEL_BLOCK_MARKERS = (
    "model_not_available",
    "model not available",
    "model does not exist",
    "not supported for this model",
    "project does not have access to the requested model",
)


@dataclass(frozen=True)
class FixtureRecord:
    stem: str
    language: str
    audio_path: Path
    reference_path: Path
    reference_text: str
    duration_seconds: float
    audio_sha256: str
    reference_sha256: str


def _split_filter_values(value: str | None) -> set[str] | None:
    values = {item.strip() for item in str(value or "").split(",") if item.strip()}
    return values or None


def _matches_filter(value: str, selected: set[str] | None) -> bool:
    return selected is None or value in selected


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return "unavailable"
    commit = completed.stdout.strip()
    return commit or "unavailable"


def _is_worktree_dirty() -> bool:
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return False
    return bool(completed.stdout.strip())


def _load_local_package():
    import sys

    src_path = str(ROOT / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def _measure_duration_seconds(audio_path: Path) -> float:
    _load_local_package()
    from easy_ai_clients.audio._transcribe.pre_processing import load_audio

    audio = load_audio(str(audio_path))
    return round(len(audio) / 1000.0, 3)


def _extract_archive(archive_path: Path, target_dir: Path) -> Path:
    if not archive_path.is_file():
        raise FileNotFoundError(f"Fixture archive not found: {archive_path}")
    with tarfile.open(archive_path, "r:xz") as archive:
        try:
            archive.extractall(target_dir, filter="data")
        except TypeError:
            archive.extractall(target_dir)
    extracted = target_dir / "audios_tests"
    if not extracted.is_dir():
        raise FileNotFoundError("Fixture archive did not contain audios_tests/.")
    return extracted


def _load_fixtures(fixtures_dir: Path) -> list[FixtureRecord]:
    if not fixtures_dir.is_dir():
        raise FileNotFoundError(f"Fixture directory not found: {fixtures_dir}")

    mp3_stems = {path.stem for path in fixtures_dir.glob("*.mp3")}
    txt_stems = {path.stem for path in fixtures_dir.glob("*.txt")}
    expected_stems = set(EXPECTED_FIXTURES)
    if mp3_stems != expected_stems or txt_stems != expected_stems:
        raise RuntimeError(
            "Fixture integrity check failed. "
            f"mp3={sorted(mp3_stems)} txt={sorted(txt_stems)} expected={sorted(expected_stems)}"
        )

    fixtures = []
    for stem in sorted(EXPECTED_FIXTURES):
        audio_path = fixtures_dir / f"{stem}.mp3"
        reference_path = fixtures_dir / f"{stem}.txt"
        reference_text = reference_path.read_text(encoding="utf-8").strip()
        if not reference_text:
            raise RuntimeError(f"Reference text is empty: {reference_path}")
        fixtures.append(
            FixtureRecord(
                stem=stem,
                language=EXPECTED_FIXTURES[stem],
                audio_path=audio_path,
                reference_path=reference_path,
                reference_text=reference_text,
                duration_seconds=_measure_duration_seconds(audio_path),
                audio_sha256=_sha256_file(audio_path),
                reference_sha256=_sha256_file(reference_path),
            )
        )
    return fixtures


def _provider_models(provider: str) -> list[str]:
    module = importlib.import_module(f"easy_ai_clients.audio._transcribe._apis.{provider}")
    models = getattr(module, "SUPPORTED_MODELS", None)
    if isinstance(models, dict):
        return list(models)
    return sorted(models or [])


def _all_provider_models() -> dict[str, list[str]]:
    _load_local_package()
    from easy_ai_clients import audio

    return {provider: _provider_models(provider) for provider in audio.available_transcribe_apis()}


def _normalize_for_metrics(text: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or "")).casefold()
    chars = []
    previous_space = True
    for char in normalized:
        category = unicodedata.category(char)
        keep = category[0] in {"L", "N", "M"}
        if keep:
            chars.append(char)
            previous_space = False
        elif not previous_space:
            chars.append(" ")
            previous_space = True
    return "".join(chars).strip()


def _metric_words(text: Any) -> list[str]:
    normalized = _normalize_for_metrics(text)
    return [item for item in normalized.split(" ") if item]


def _metric_chars(text: Any) -> list[str]:
    normalized = _normalize_for_metrics(text)
    return [char for char in normalized.replace(" ", "")]


def _levenshtein_distance(left: list[str], right: list[str]) -> int:
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


def _quality_metrics(reference: str, observed: str) -> dict[str, Any]:
    reference_words = _metric_words(reference)
    observed_words = _metric_words(observed)
    reference_chars = _metric_chars(reference)
    observed_chars = _metric_chars(observed)

    if reference_words:
        word_distance = _levenshtein_distance(reference_words, observed_words)
        wer = word_distance / len(reference_words)
        word_accuracy = max(0.0, 1.0 - wer)
    else:
        wer = 0.0 if not observed_words else 1.0
        word_accuracy = 1.0 if not observed_words else 0.0

    if reference_chars:
        char_distance = _levenshtein_distance(reference_chars, observed_chars)
        cer = char_distance / len(reference_chars)
        char_similarity = max(0.0, 1.0 - cer)
    else:
        cer = 0.0 if not observed_chars else 1.0
        char_similarity = 1.0 if not observed_chars else 0.0

    return {
        "wer": round(wer, 6),
        "word_accuracy": round(word_accuracy, 6),
        "word_accuracy_percent": round(word_accuracy * 100.0, 2),
        "cer": round(cer, 6),
        "char_similarity": round(char_similarity, 6),
        "char_similarity_percent": round(char_similarity * 100.0, 2),
        "reference_word_count": len(reference_words),
        "transcript_word_count": len(observed_words),
        "reference_char_count": len(reference_chars),
        "transcript_char_count": len(observed_chars),
    }


def _compact_text(value: Any, limit: int = 600) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _redact_secrets(message: Any) -> str:
    cleaned = _compact_text(message, limit=1000)
    for env_var in PROVIDER_ENV.values():
        secret = str(os.getenv(env_var) or "").strip()
        if len(secret) >= 6:
            cleaned = cleaned.replace(secret, "[redacted]")
    project_id = str(os.getenv("DEEPGRAM_PROJECT_ID") or "").strip()
    if len(project_id) >= 6:
        cleaned = cleaned.replace(project_id, "[redacted]")
    cleaned = re.sub(r"(?i)(authorization\s*[:=]\s*(?:bearer|key|token)?\s*)[^\s,;]+", r"\1[redacted]", cleaned)
    cleaned = re.sub(r"(?i)\b(api[_-]?key|token|secret)(\s*[:=]\s*)[^\s,;]+", r"\1\2[redacted]", cleaned)
    return cleaned


def _classify_error(error: Any) -> str:
    message = str(error or "").casefold()
    if any(marker in message for marker in ACCOUNT_BLOCK_MARKERS):
        return "account_or_credit_blocked"
    if any(marker in message for marker in MODEL_BLOCK_MARKERS):
        return "model_or_access_blocked"
    if any(marker in message for marker in TRANSIENT_ERROR_MARKERS):
        return "transient_failure"
    return "failed"


def _cost_status(row: dict[str, Any]) -> str:
    source = row.get("cost_source")
    error = str(row.get("cost_lookup_error") or "").casefold()
    if row.get("status") != "ok":
        return row.get("status", "failed")
    if source == "provider_response":
        return "exact_returned_immediately"
    if source == "usage_lookup":
        return "exact_obtained_by_lookup"
    if source == "pricing_api_billable_units":
        return "estimated_pricing_api_billable_units"
    if source == "pricing_api":
        return "estimated_pricing_api"
    if source == "official_pricing_table":
        return "estimated_official_pricing_table"
    if source == "unavailable" and any(marker in error for marker in ("permission", "scope", "403", "forbidden")):
        return "unavailable_permission_blocked"
    if source == "unavailable":
        return "unavailable_provider_or_lookup"
    return "unknown"


def _row_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("provider") or ""),
        str(row.get("model") or ""),
        str(row.get("audio") or ""),
        str(row.get("language_mode") or ""),
    )


def _split_markdown_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]

    cells = []
    current = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return [html.unescape(cell.replace("<br>", "\n")) for cell in cells]


def _parse_optional_float(value: Any) -> float | None:
    text = str(value or "").strip().removesuffix("%")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_optional_bool(value: Any) -> bool | None:
    text = str(value or "").strip().casefold()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _parse_language_cell(value: str) -> tuple[str, str]:
    if ": " not in value:
        return value, ""
    parameter, code = value.split(": ", 1)
    return parameter, code


def _parse_details_section(markdown_text: str) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    if "## Returned Transcripts And Errors" not in markdown_text:
        return {}
    section = markdown_text.split("## Returned Transcripts And Errors", 1)[1]
    section = section.split("## Rerun Instructions", 1)[0]
    details: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    pattern = re.compile(r"<details><summary>(.*?)</summary>(.*?)</details>", re.DOTALL)
    for match in pattern.finditer(section):
        summary = html.unescape(match.group(1).strip())
        summary_match = re.match(r"\d+\.\s+(.*?) / (.*?) / (.*?) / (.*?) / (.*)", summary)
        if not summary_match:
            continue
        provider, model, audio_name, mode, status = summary_match.groups()
        key = (provider, model, audio_name, mode)
        body = match.group(2)
        field_values: dict[str, str] = {"status": status}

        for line in body.splitlines():
            if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Field"):
                continue
            cells = _split_markdown_row(line)
            if len(cells) == 2:
                field_values[cells[0]] = cells[1]

        transcript_match = re.search(r"<pre>\s*(.*?)\s*</pre>", body, re.DOTALL)
        field_values["transcript"] = html.unescape(transcript_match.group(1) if transcript_match else "")
        details[key] = field_values

    return details


def _parse_existing_benchmark_doc(doc_path: Path) -> list[dict[str, Any]]:
    if not doc_path.is_file():
        raise FileNotFoundError(f"Existing benchmark report not found: {doc_path}")

    markdown_text = doc_path.read_text(encoding="utf-8")
    if "## Detailed Results" not in markdown_text:
        raise RuntimeError(f"Benchmark report has no Detailed Results section: {doc_path}")

    details_by_key = _parse_details_section(markdown_text)
    detailed_section = markdown_text.split("## Detailed Results", 1)[1]
    detailed_section = detailed_section.split("## Returned Transcripts And Errors", 1)[0]
    rows: list[dict[str, Any]] = []

    for line in detailed_section.splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Provider"):
            continue
        cells = _split_markdown_row(line)
        if len(cells) != 16:
            continue
        (
            provider,
            model,
            audio_name,
            mode,
            language_cell,
            returned_language,
            elapsed,
            duration,
            wer,
            word_accuracy,
            cer,
            char_similarity,
            cost_usd,
            cost_status,
            request_id,
            status,
        ) = cells
        language_parameter, language_code = _parse_language_cell(language_cell)
        key = (provider, model, audio_name, mode)
        details = details_by_key.get(key, {})

        row = {
            "provider": provider,
            "model": model,
            "audio": audio_name,
            "fixture_language": EXPECTED_FIXTURES.get(audio_name, ""),
            "language_mode": mode,
            "language_parameter": details.get("language parameter", language_parameter),
            "language_code": details.get("language code", language_code),
            "duration_seconds": _parse_optional_float(duration),
            "status": status,
            "started_at": "",
            "ended_at": "",
            "elapsed_seconds": _parse_optional_float(elapsed),
            "returned_language": details.get("returned language", returned_language),
            "request_id": details.get("request_id", request_id),
            "cost_usd": _parse_optional_float(cost_usd),
            "cost_source": details.get("cost_source", ""),
            "cost_is_estimated": _parse_optional_bool(details.get("cost_is_estimated", "")),
            "cost_lookup_error": details.get("cost_lookup_error", ""),
            "cost_update_attempted": _parse_optional_bool(details.get("cost_update_attempted", "")),
            "cost_update_error": "",
            "cost_status": cost_status,
            "transcript": details.get("transcript", ""),
            "error_type": details.get("error_type", ""),
            "error_message": details.get("error_message", ""),
            "wer": _parse_optional_float(wer),
            "word_accuracy_percent": _parse_optional_float(word_accuracy),
            "cer": _parse_optional_float(cer),
            "char_similarity_percent": _parse_optional_float(char_similarity),
            "reference_word_count": 0,
            "transcript_word_count": 0,
            "reference_char_count": 0,
            "transcript_char_count": 0,
        }
        rows.append(row)

    if not rows:
        raise RuntimeError(f"No benchmark rows could be parsed from: {doc_path}")
    return rows


def _merge_rows(existing_rows: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    new_by_key = {_row_key(row): row for row in new_rows}
    replaced = 0
    merged = []
    seen_keys = set()

    for row in existing_rows:
        key = _row_key(row)
        if key in new_by_key:
            merged.append(new_by_key[key])
            seen_keys.add(key)
            replaced += 1
        else:
            merged.append(row)

    for key, row in new_by_key.items():
        if key not in seen_keys:
            merged.append(row)
    return merged, replaced


def _request_id_text(result: dict[str, Any] | None) -> str:
    if not result:
        return ""
    request_id = result.get("request_id")
    if isinstance(request_id, list):
        return ", ".join(str(item) for item in request_id if item)
    if isinstance(request_id, tuple):
        return ", ".join(str(item) for item in request_id if item)
    return str(request_id or "")


def _explicit_language_kwargs(provider: str, model: str, fixture: FixtureRecord) -> tuple[dict[str, str] | None, str, str]:
    config = EXPLICIT_LANGUAGE_CODES.get(provider)
    if not config:
        return None, "", "unsupported"
    if model in set(config.get("unsupported_models") or []):
        return None, str(config["parameter"]), "unsupported"
    if provider == "deepgram":
        code = (DEEPGRAM_MODEL_LANGUAGE_CODES.get(model) or {}).get(fixture.stem)
    else:
        code = (config.get("codes") or {}).get(fixture.stem)
    if not code:
        return None, str(config["parameter"]), "unsupported"
    parameter = str(config["parameter"])
    return {parameter: code}, parameter, code


def _run_with_retries(callable_object, *, max_attempts: int, retry_wait_seconds: float):
    last_error = None
    for attempt in range(1, max(1, int(max_attempts)) + 1):
        try:
            return callable_object(), None, attempt
        except Exception as error:
            last_error = error
            classification = _classify_error(error)
            if classification != "transient_failure" or attempt >= max_attempts:
                return None, error, attempt
            time.sleep(float(retry_wait_seconds) * attempt)
    return None, last_error, max_attempts


def _maybe_update_cost(provider: str, result: dict[str, Any], args) -> tuple[dict[str, Any], bool, str | None]:
    if provider != "deepgram" or not result.get("request_id"):
        return result, False, None

    _load_local_package()
    from easy_ai_clients import audio

    updated = dict(result)
    lookup_error = None
    for attempt in range(1, max(1, int(args.cost_lookup_retries)) + 1):
        try:
            updated = audio.update_cost("transcribe", updated, api=provider)
        except Exception as error:
            lookup_error = _redact_secrets(error)
            break
        lookup_error = updated.get("cost_lookup_error")
        if updated.get("cost_source") == "usage_lookup":
            break
        if lookup_error and any(marker in str(lookup_error).casefold() for marker in ("403", "scope", "permission", "forbidden")):
            break
        if attempt < args.cost_lookup_retries:
            time.sleep(float(args.cost_lookup_wait_seconds))
    return updated, True, _redact_secrets(lookup_error)


def _empty_row(provider: str, model: str, fixture: FixtureRecord, mode: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "audio": fixture.stem,
        "fixture_language": fixture.language,
        "language_mode": mode,
        "language_parameter": "",
        "language_code": "",
        "duration_seconds": fixture.duration_seconds,
        "status": "not_run",
        "started_at": "",
        "ended_at": "",
        "elapsed_seconds": None,
        "returned_language": "",
        "request_id": "",
        "cost_usd": None,
        "cost_source": "",
        "cost_is_estimated": None,
        "cost_lookup_error": "",
        "cost_update_attempted": False,
        "cost_update_error": "",
        "cost_status": "not_run",
        "transcript": "",
        "error_type": "",
        "error_message": "",
        "wer": None,
        "word_accuracy_percent": None,
        "cer": None,
        "char_similarity_percent": None,
        "reference_word_count": 0,
        "transcript_word_count": 0,
        "reference_char_count": 0,
        "transcript_char_count": 0,
    }


def _run_case(provider: str, model: str, fixture: FixtureRecord, mode: str, args) -> dict[str, Any]:
    _load_local_package()
    from easy_ai_clients import audio

    row = _empty_row(provider, model, fixture, mode)
    kwargs: dict[str, Any] = {}
    if mode == "auto":
        row["language_parameter"] = "auto/default"
        row["language_code"] = AUTO_LANGUAGE_NOTES.get(provider, "automatic language detection")
    else:
        explicit_kwargs, parameter, code = _explicit_language_kwargs(provider, model, fixture)
        row["language_parameter"] = parameter
        row["language_code"] = code
        if explicit_kwargs is None:
            row["status"] = "unsupported"
            row["error_message"] = "Explicit language selection is not supported for this provider/model."
            row["cost_status"] = _cost_status(row)
            return row
        kwargs.update(explicit_kwargs)

    started_at = datetime.now(UTC)
    row["started_at"] = started_at.isoformat(timespec="seconds")
    started = time.perf_counter()

    def call_provider():
        return audio.transcribe(str(fixture.audio_path), api=provider, model=model, **kwargs)

    result, error, attempts = _run_with_retries(
        call_provider,
        max_attempts=args.max_attempts,
        retry_wait_seconds=args.retry_wait_seconds,
    )
    row["attempts"] = attempts
    row["ended_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    row["elapsed_seconds"] = round(time.perf_counter() - started, 3)

    if error is not None:
        row["status"] = _classify_error(error)
        row["error_type"] = type(error).__name__
        row["error_message"] = _redact_secrets(error)
        row["cost_status"] = _cost_status(row)
        return row

    assert isinstance(result, dict)
    result, cost_update_attempted, cost_update_error = _maybe_update_cost(provider, result, args)
    transcript = str(result.get("text") or "")
    metrics = _quality_metrics(fixture.reference_text, transcript)
    row.update(metrics)
    row.update(
        {
            "status": "ok",
            "returned_language": str(result.get("language") or ""),
            "request_id": _request_id_text(result),
            "cost_usd": result.get("cost_usd"),
            "cost_source": str(result.get("cost_source") or ""),
            "cost_is_estimated": result.get("cost_is_estimated"),
            "cost_lookup_error": _redact_secrets(result.get("cost_lookup_error")),
            "cost_update_attempted": cost_update_attempted,
            "cost_update_error": _redact_secrets(cost_update_error),
            "transcript": transcript,
            "provider_metadata_keys": ", ".join(sorted((result.get("provider_metadata") or {}).keys())),
        }
    )
    row["cost_status"] = _cost_status(row)
    return row


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\n", "<br>")
    return text.replace("|", r"\|")


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(_markdown_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(item) for item in row) + " |")
    return "\n".join(lines)


def _fmt_float(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_cost(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):.6f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _primary_metric(row: dict[str, Any]) -> float:
    if row.get("audio") == "Mandarin":
        return float(row.get("char_similarity_percent") or 0.0)
    return float(row.get("word_accuracy_percent") or 0.0)


def _best_by_key(rows: list[dict[str, Any]], key_name: str) -> dict[str, dict[str, Any]]:
    best = {}
    for row in rows:
        if row.get("status") != "ok":
            continue
        key = str(row.get(key_name))
        if key not in best or _primary_metric(row) > _primary_metric(best[key]):
            best[key] = row
    return best


def _average_success_by_model(rows: list[dict[str, Any]]) -> list[tuple[str, str, int, float, float, float]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("status") == "ok":
            grouped[(str(row["provider"]), str(row["model"]))].append(row)
    summary = []
    for (provider, model), items in grouped.items():
        word_accuracy = sum(float(item.get("word_accuracy_percent") or 0.0) for item in items) / len(items)
        char_similarity = sum(float(item.get("char_similarity_percent") or 0.0) for item in items) / len(items)
        elapsed = sum(float(item.get("elapsed_seconds") or 0.0) for item in items) / len(items)
        summary.append((provider, model, len(items), word_accuracy, char_similarity, elapsed))
    return sorted(summary, key=lambda item: (-item[4], item[5], item[0], item[1]))


def _write_markdown_doc(
    rows: list[dict[str, Any]],
    fixtures: list[FixtureRecord],
    provider_models: dict[str, list[str]],
    skipped_providers: dict[str, str],
    archive_path: Path,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    _load_local_package()
    import easy_ai_clients

    archive_sha = _sha256_file(archive_path) if archive_path.is_file() else "missing"
    archive_size = archive_path.stat().st_size if archive_path.is_file() else 0
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    status_counts = Counter(str(row.get("status")) for row in rows)
    cost_counts = Counter(str(row.get("cost_status")) for row in rows)
    failures = [row for row in rows if row.get("status") not in {"ok", "unsupported"}]

    lines = [
        "# Live Multilingual Transcription Benchmark",
        "",
        f"- Generated / last updated: `{finished_at.isoformat(timespec='seconds')}`",
        f"- Latest runner started: `{started_at.isoformat(timespec='seconds')}`",
        f"- Package version: `{easy_ai_clients.__version__}`",
        f"- Git commit: `{_repo_commit()}`" + (" (dirty worktree)" if _is_worktree_dirty() else ""),
        f"- Fixture archive: `{archive_path.relative_to(ROOT).as_posix()}`",
        f"- Fixture archive SHA-256: `{archive_sha}`",
        f"- Fixture archive size: `{archive_size}` bytes",
        "",
        "## Methodology",
        "",
        "This benchmark runs real paid transcription calls sequentially. Each provider/model/audio pair is tested in automatic language detection mode and, when supported, in explicit language mode. The runner loads root `.env` with `python-dotenv` and skips providers whose credential is absent.",
        "",
        "Text metrics are computed without translating text. The runner applies Unicode NFKC normalization, case folding, punctuation/symbol removal, whitespace collapsing, and then computes WER from whitespace-delimited tokens. It also computes CER and normalized character similarity from punctuation-free, whitespace-free characters. For Mandarin, character similarity is treated as the primary quality signal because whitespace tokenization is weak.",
        "",
        "Cost fields come from the normalized `easy_ai_clients.audio.transcribe(...)` result. When a library cost refresh helper exists, the runner uses it after a successful call. Unknown cost remains distinct from free: `cost_usd=None` and `cost_source=\"unavailable\"`.",
        "",
        "## Provider And Model Surface",
        "",
        _markdown_table(
            ["Provider", "Credential", "Models tested", "Automatic language behavior"],
            [
                [
                    provider,
                    PROVIDER_ENV.get(provider, ""),
                    ", ".join(models),
                    AUTO_LANGUAGE_NOTES.get(provider, ""),
                ]
                for provider, models in provider_models.items()
            ],
        ),
        "",
        "## Explicit Language Map",
        "",
        _markdown_table(
            ["Provider", "Parameter", *EXPECTED_FIXTURES.keys()],
            [
                [
                    provider,
                    config.get("parameter", ""),
                    *[(config.get("codes") or {}).get(stem, "unsupported") for stem in EXPECTED_FIXTURES],
                ]
                for provider, config in EXPLICIT_LANGUAGE_CODES.items()
            ],
        ),
        "",
        "## Provider/Model Input Limits",
        "",
        "These limits are official provider-published limits for the endpoint or model pages reviewed. "
        "When the exact transcription endpoint/model does not publish a duration or file-size limit, "
        "the table says so explicitly instead of inferring one from these small benchmark fixtures.",
        "",
        _markdown_table(
            [
                "Provider",
                "Models",
                "Endpoint/mode used",
                "Max duration",
                "Max file/body size",
                "Format/request notes",
                "Source",
                "Status",
            ],
            [
                [
                    row["provider"],
                    row["models"],
                    row["endpoint"],
                    row["max_duration"],
                    row["max_size"],
                    row["format_notes"],
                    row["source"],
                    row["status"],
                ]
                for row in INPUT_LIMIT_ROWS
                if row["provider"] in provider_models
            ],
        ),
        "",
        "Deepgram explicit language support is model-specific. Unsupported fixture/model pairs are documented as `unsupported` instead of being sent as paid calls.",
        "",
        _markdown_table(
            ["Deepgram model", "Explicit fixture codes"],
            [
                [
                    model,
                    ", ".join(f"{fixture}: {code}" for fixture, code in sorted(codes.items())),
                ]
                for model, codes in sorted(DEEPGRAM_MODEL_LANGUAGE_CODES.items())
            ],
        ),
        "",
        "## Cost Methodology",
        "",
    ]

    for provider in provider_models:
        links = " ".join(f"[{index + 1}]({link})" for index, link in enumerate(OFFICIAL_REFERENCE_LINKS.get(provider, [])))
        lines.extend([f"### `{provider}`", "", COST_METHOD_NOTES.get(provider, ""), "", f"Official references: {links}", ""])

    lines.extend(
        [
            "## Fixtures",
            "",
            _markdown_table(
                ["Audio", "Language", "Measured duration (s)", "Audio SHA-256", "Reference SHA-256"],
                [
                    [
                        fixture.stem,
                        fixture.language,
                        _fmt_float(fixture.duration_seconds, 3),
                        fixture.audio_sha256,
                        fixture.reference_sha256,
                    ]
                    for fixture in fixtures
                ],
            ),
            "",
        ]
    )

    for fixture in fixtures:
        lines.extend(
            [
                f"<details><summary>Reference: {fixture.stem}</summary>",
                "",
                "<pre>",
                html.escape(fixture.reference_text),
                "</pre>",
                "",
                "</details>",
                "",
            ]
        )

    lines.extend(
        [
            "## Summary",
            "",
            "### Status Counts",
            "",
            _markdown_table(["Status", "Count"], [[key, status_counts[key]] for key in sorted(status_counts)]),
            "",
            "### Cost Status Counts",
            "",
            _markdown_table(["Cost status", "Count"], [[key, cost_counts[key]] for key in sorted(cost_counts)]),
            "",
        ]
    )

    if skipped_providers:
        lines.extend(
            [
                "### Skipped Providers",
                "",
                _markdown_table(
                    ["Provider", "Reason"],
                    [[provider, reason] for provider, reason in sorted(skipped_providers.items())],
                ),
                "",
            ]
        )

    best_by_audio = _best_by_key(ok_rows, "audio")
    lines.extend(
        [
            "### Best Accuracy By Audio",
            "",
            _markdown_table(
                ["Audio", "Provider", "Model", "Mode", "WER", "Word accuracy", "CER", "Char similarity"],
                [
                    [
                        audio_name,
                        row["provider"],
                        row["model"],
                        row["language_mode"],
                        _fmt_float(row.get("wer"), 3),
                        _fmt_float(row.get("word_accuracy_percent"), 2) + "%",
                        _fmt_float(row.get("cer"), 3),
                        _fmt_float(row.get("char_similarity_percent"), 2) + "%",
                    ]
                    for audio_name, row in sorted(best_by_audio.items())
                ],
            ),
            "",
            "### Average Successful Quality By Provider/Model",
            "",
            _markdown_table(
                ["Provider", "Model", "Successful calls", "Avg word accuracy", "Avg char similarity", "Avg elapsed (s)"],
                [
                    [provider, model, count, f"{word_accuracy:.2f}%", f"{char_similarity:.2f}%", f"{elapsed:.3f}"]
                    for provider, model, count, word_accuracy, char_similarity, elapsed in _average_success_by_model(ok_rows)
                ],
            ),
            "",
        ]
    )

    fastest = {}
    cheapest = {}
    for row in ok_rows:
        audio_name = str(row["audio"])
        elapsed = row.get("elapsed_seconds")
        if elapsed is not None and (audio_name not in fastest or float(elapsed) < float(fastest[audio_name].get("elapsed_seconds") or 999999)):
            fastest[audio_name] = row
        if row.get("cost_usd") is not None and (audio_name not in cheapest or float(row["cost_usd"]) < float(cheapest[audio_name].get("cost_usd") or 999999)):
            cheapest[audio_name] = row

    lines.extend(
        [
            "### Fastest Successful Result By Audio",
            "",
            _markdown_table(
                ["Audio", "Provider", "Model", "Mode", "Elapsed (s)", "Word accuracy", "Char similarity"],
                [
                    [
                        audio_name,
                        row["provider"],
                        row["model"],
                        row["language_mode"],
                        _fmt_float(row.get("elapsed_seconds"), 3),
                        _fmt_float(row.get("word_accuracy_percent"), 2) + "%",
                        _fmt_float(row.get("char_similarity_percent"), 2) + "%",
                    ]
                    for audio_name, row in sorted(fastest.items())
                ],
            ),
            "",
            "### Cheapest Known Or Estimated Result By Audio",
            "",
            _markdown_table(
                ["Audio", "Provider", "Model", "Mode", "Cost USD", "Cost status"],
                [
                    [
                        audio_name,
                        row["provider"],
                        row["model"],
                        row["language_mode"],
                        _fmt_cost(row.get("cost_usd")),
                        row["cost_status"],
                    ]
                    for audio_name, row in sorted(cheapest.items())
                ],
            ),
            "",
        ]
    )

    if failures:
        lines.extend(
            [
                "### Failures, Credit, Quota, And Access Blockers",
                "",
                _markdown_table(
                    ["Provider", "Model", "Audio", "Mode", "Status", "Error"],
                    [
                        [
                            row["provider"],
                            row["model"],
                            row["audio"],
                            row["language_mode"],
                            row["status"],
                            _compact_text(row.get("error_message"), 240),
                        ]
                        for row in failures
                    ],
                ),
                "",
            ]
        )
        if any(
            row["provider"] == "fireworks"
            and row["model"] == "whisper-v3-turbo"
            and str(row["status"]).startswith("account_or_credit_blocked")
            for row in failures
        ):
            lines.extend(
                [
                    "Fireworks `whisper-v3-turbo` was partially exercised before the "
                    "account returned HTTP 401 Unauthorized. Rerun that model after "
                    "the Fireworks key, billing, or model access is corrected.",
                    "",
                ]
            )
        if any(
            row["provider"] == "speechmatics"
            and row["language_mode"] == "auto"
            and row["status"] == "failed"
            and "identified language" in str(row.get("error_message", "")).casefold()
            for row in failures
        ):
            lines.extend(
                [
                    "Speechmatics `language='auto'` rejected the Bengali and Urdu "
                    "fixtures after detecting `bn`/`ur`; explicit `language='bn'` "
                    "and `language='ur'` completed successfully.",
                    "",
                ]
            )

    lines.extend(
        [
            "## Detailed Results",
            "",
            _markdown_table(
                [
                    "Provider",
                    "Model",
                    "Audio",
                    "Mode",
                    "Lang param/code",
                    "Returned lang",
                    "Elapsed (s)",
                    "Duration (s)",
                    "WER",
                    "Word acc",
                    "CER",
                    "Char sim",
                    "Cost USD",
                    "Cost status",
                    "Request ID",
                    "Status",
                ],
                [
                    [
                        row["provider"],
                        row["model"],
                        row["audio"],
                        row["language_mode"],
                        f"{row.get('language_parameter')}: {row.get('language_code')}",
                        row.get("returned_language"),
                        _fmt_float(row.get("elapsed_seconds"), 3),
                        _fmt_float(row.get("duration_seconds"), 3),
                        _fmt_float(row.get("wer"), 3),
                        (_fmt_float(row.get("word_accuracy_percent"), 2) + "%") if row.get("word_accuracy_percent") is not None else "",
                        _fmt_float(row.get("cer"), 3),
                        (_fmt_float(row.get("char_similarity_percent"), 2) + "%") if row.get("char_similarity_percent") is not None else "",
                        _fmt_cost(row.get("cost_usd")),
                        row.get("cost_status"),
                        _compact_text(row.get("request_id"), 80),
                        row.get("status"),
                    ]
                    for row in rows
                ],
            ),
            "",
            "## Returned Transcripts And Errors",
            "",
        ]
    )

    for index, row in enumerate(rows, start=1):
        title = f"{index}. {row['provider']} / {row['model']} / {row['audio']} / {row['language_mode']} / {row['status']}"
        lines.extend([f"<details><summary>{html.escape(title)}</summary>", ""])
        lines.extend(
            [
                _markdown_table(
                    ["Field", "Value"],
                    [
                        ["language parameter", row.get("language_parameter")],
                        ["language code", row.get("language_code")],
                        ["returned language", row.get("returned_language")],
                        ["elapsed seconds", row.get("elapsed_seconds")],
                        ["request_id", row.get("request_id")],
                        ["cost_usd", _fmt_cost(row.get("cost_usd"))],
                        ["cost_source", row.get("cost_source")],
                        ["cost_is_estimated", row.get("cost_is_estimated")],
                        ["cost_lookup_error", row.get("cost_lookup_error")],
                        ["cost_update_attempted", row.get("cost_update_attempted")],
                        ["error_type", row.get("error_type")],
                        ["error_message", row.get("error_message")],
                    ],
                ),
                "",
                "**Transcript**",
                "",
                "<pre>",
                html.escape(str(row.get("transcript") or "")),
                "</pre>",
                "",
                "</details>",
                "",
            ]
        )

    lines.extend(
        [
            "## Rerun Instructions",
            "",
            "Full matrix:",
            "",
            "```powershell",
            "$env:EASY_AI_CLIENTS_LIVE_TRANSCRIBE_MULTILINGUAL = '1'",
            "python tests/test_live_transcribe_multilingual_matrix.py",
            "```",
            "",
            "Run through pytest instead of the direct script entrypoint:",
            "",
            "```powershell",
            "$env:EASY_AI_CLIENTS_LIVE_TRANSCRIBE_MULTILINGUAL = '1'",
            "pytest tests/test_live_transcribe_multilingual_matrix.py -s",
            "```",
            "",
            "Rerun a subset:",
            "",
            "```powershell",
            "$env:EASY_AI_CLIENTS_LIVE_TRANSCRIBE_MULTILINGUAL = '1'",
            "python tests/test_live_transcribe_multilingual_matrix.py "
            "--provider deepgram --model nova-3 --audio Portuguese-BR --mode explicit "
            "--doc docs/audio/transcribe/live_multilingual_benchmark_rerun.md",
            "```",
            "",
            "Merge only failed, missing, or blocked rows back into this report:",
            "",
            "```powershell",
            "$env:EASY_AI_CLIENTS_LIVE_TRANSCRIBE_MULTILINGUAL = '1'",
            "python tests/test_live_transcribe_multilingual_matrix.py "
            "--provider fireworks --model whisper-v3-turbo --only-missing-or-blocked "
            "--doc docs/audio/transcribe/live_multilingual_benchmark.md",
            "```",
            "",
            "Equivalent environment filters for pytest:",
            "",
            "```powershell",
            "$env:EASY_AI_CLIENTS_LIVE_TRANSCRIBE_MULTILINGUAL = '1'",
            "$env:EASY_AI_CLIENTS_BENCHMARK_PROVIDERS = 'together'",
            "$env:EASY_AI_CLIENTS_BENCHMARK_AUDIOS = 'Mandarin,Portuguese-BR'",
            "$env:EASY_AI_CLIENTS_BENCHMARK_MODES = 'auto,explicit'",
            "pytest tests/test_live_transcribe_multilingual_matrix.py -s",
            "```",
            "",
            "The runner requires provider credentials in root `.env`. Do not commit "
            "secrets. If credits or model access are added later, rerun only the "
            "affected provider/model/audio/mode subset with the filters above. Omit "
            "`--doc` only when intentionally replacing this complete benchmark report.",
            "",
        ]
    )

    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", action="append", help="Provider filter; may be repeated.")
    parser.add_argument("--model", action="append", help="Model filter; may be repeated.")
    parser.add_argument("--audio", action="append", help="Audio fixture stem filter; may be repeated.")
    parser.add_argument("--mode", action="append", choices=("auto", "explicit"), help="Language mode filter; may be repeated.")
    parser.add_argument("--archive", type=Path, default=ARCHIVE_PATH, help="Fixture archive path.")
    parser.add_argument("--doc", type=Path, default=DOC_PATH, help="Markdown output path.")
    parser.add_argument("--max-attempts", type=int, default=2, help="Attempts for transient provider failures.")
    parser.add_argument("--retry-wait-seconds", type=float, default=5.0, help="Base wait for transient retry backoff.")
    parser.add_argument("--cost-lookup-retries", type=int, default=2, help="Deepgram post-hoc cost lookup attempts.")
    parser.add_argument("--cost-lookup-wait-seconds", type=float, default=5.0, help="Wait between eventual cost lookup retries.")
    parser.add_argument("--validate-fixtures-only", action="store_true", help="Validate archive/fixtures and write no docs.")
    parser.add_argument(
        "--only-missing-or-blocked",
        action="store_true",
        help="Parse --doc, run only selected rows whose existing status is failed/blocked/missing, then merge.",
    )
    return parser


def _merge_cli_and_env_filters(args) -> dict[str, set[str] | None]:
    return {
        "providers": set(args.provider or []) or _split_filter_values(os.getenv(FILTER_ENV_VARS["providers"])),
        "models": set(args.model or []) or _split_filter_values(os.getenv(FILTER_ENV_VARS["models"])),
        "audios": set(args.audio or []) or _split_filter_values(os.getenv(FILTER_ENV_VARS["audios"])),
        "modes": set(args.mode or []) or _split_filter_values(os.getenv(FILTER_ENV_VARS["modes"])),
    }


def run_benchmark(args) -> list[dict[str, Any]]:
    global DOC_PATH
    DOC_PATH = args.doc

    load_dotenv(ROOT / ".env", override=True)
    _load_local_package()
    provider_models = _all_provider_models()
    filters = _merge_cli_and_env_filters(args)
    rows: list[dict[str, Any]] = []
    skipped_providers: dict[str, str] = {}
    started_at = datetime.now(UTC)
    existing_rows: list[dict[str, Any]] = []
    existing_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if args.only_missing_or_blocked:
        existing_rows = _parse_existing_benchmark_doc(args.doc)
        existing_by_key = {_row_key(row): row for row in existing_rows}

    with tempfile.TemporaryDirectory(prefix="easy-ai-clients-transcribe-") as temp_name:
        extracted_dir = _extract_archive(args.archive, Path(temp_name))
        fixtures = _load_fixtures(extracted_dir)

        if args.validate_fixtures_only:
            return []

        selected_fixtures = [fixture for fixture in fixtures if _matches_filter(fixture.stem, filters["audios"])]
        selected_modes = [mode for mode in ("auto", "explicit") if _matches_filter(mode, filters["modes"])]

        for provider, models in provider_models.items():
            if not _matches_filter(provider, filters["providers"]):
                continue
            env_var = PROVIDER_ENV.get(provider)
            if env_var and not os.getenv(env_var):
                skipped_providers[provider] = f"Missing {env_var}"
                continue

            provider_blocker = None
            model_blockers: dict[str, str] = {}
            for model in models:
                if not _matches_filter(model, filters["models"]):
                    continue
                for fixture in selected_fixtures:
                    for mode in selected_modes:
                        key = (provider, model, fixture.stem, mode)
                        existing_row = existing_by_key.get(key)
                        if args.only_missing_or_blocked and (
                            existing_row is not None
                            and str(existing_row.get("status")) not in RERUNNABLE_STATUSES
                        ):
                            continue

                        if provider_blocker:
                            row = _empty_row(provider, model, fixture, mode)
                            row["status"] = "account_or_credit_blocked_not_retried"
                            row["error_message"] = provider_blocker
                            row["cost_status"] = _cost_status(row)
                        elif model in model_blockers:
                            row = _empty_row(provider, model, fixture, mode)
                            row["status"] = "model_or_access_blocked_not_retried"
                            row["error_message"] = model_blockers[model]
                            row["cost_status"] = _cost_status(row)
                        else:
                            row = _run_case(provider, model, fixture, mode, args)
                            if row["status"] == "account_or_credit_blocked":
                                provider_blocker = row["error_message"]
                            elif row["status"] == "model_or_access_blocked":
                                model_blockers[model] = row["error_message"]

                        rows.append(row)
                        print(
                            f"{row['provider']} | {row['model']} | {row['audio']} | "
                            f"{row['language_mode']} | {row['status']} | "
                            f"elapsed={row.get('elapsed_seconds')} | "
                            f"wer={_fmt_float(row.get('wer'), 3)} | "
                            f"word_acc={_fmt_float(row.get('word_accuracy_percent'), 2)} | "
                            f"char_sim={_fmt_float(row.get('char_similarity_percent'), 2)} | "
                            f"cost={_fmt_cost(row.get('cost_usd'))} | "
                            f"cost_status={row.get('cost_status')}"
                        )

        output_rows = rows
        output_provider_models = {
            provider: models
            for provider, models in provider_models.items()
            if _matches_filter(provider, filters["providers"])
        }
        if args.only_missing_or_blocked:
            output_rows, replaced = _merge_rows(existing_rows, rows)
            output_provider_models = provider_models
            print(f"merged {len(rows)} rerun rows into {len(output_rows)} existing benchmark rows; replaced={replaced}")

        _write_markdown_doc(
            output_rows,
            fixtures,
            output_provider_models,
            skipped_providers,
            args.archive,
            started_at,
            datetime.now(UTC),
        )

    return output_rows if args.only_missing_or_blocked else rows


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if os.getenv(LIVE_ENV_VAR) != "1" and not args.validate_fixtures_only:
        raise SystemExit(f"Set {LIVE_ENV_VAR}=1 to run paid multilingual live transcription calls.")
    run_benchmark(args)
    return 0


def test_live_transcribe_multilingual_matrix():
    if os.getenv(LIVE_ENV_VAR) != "1":
        pytest.skip(f"live multilingual transcription benchmark is gated by {LIVE_ENV_VAR}=1")
    assert main([]) == 0


if __name__ == "__main__":
    raise SystemExit(main())
