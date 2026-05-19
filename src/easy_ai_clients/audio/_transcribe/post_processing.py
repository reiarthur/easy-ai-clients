"""Provides post-processing utilities for normalized transcription payloads.

Last updated: 2026-04-21
"""

import math
import os
import re

_SEGMENT_JOIN_GAP_SECONDS = 3.0
_SEGMENT_MAX_SECONDS = 120.0
_SEGMENT_TARGET_SECONDS = 90.0
_SPLIT_WINDOW_SECONDS = 10.0
_WORD_GROUP_MAX_WINDOW_SECONDS = 1.2
_WORD_GROUP_MAX_WORDS = 4
_SILENCE_MIN_GAP_SECONDS = 0.2
_STRONG_PUNCTUATION_RE = re.compile(r"[.!?;:…]")
_COMMA_RE = re.compile(r",")
_WORD_RE = re.compile(
    r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:['’-][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)*",
    flags=re.UNICODE,
)
_VALID_MKD_LANGUAGES = {"en", "zh", "hi", "es", "fr", "ar", "bn", "pt", "ru", "ur"}
_VALID_COST_SOURCES = {
    "provider_response",
    "usage_lookup",
    "pricing_api",
    "pricing_api_billable_units",
    "official_pricing_table",
    "unavailable",
}
_COST_SECRET_ENV_VARS = (
    "DEEPGRAM_API_KEY",
    "ELEVENLABS_API_KEY",
    "FAL_KEY",
    "FIREWORKS_API_KEY",
    "SPEECHMATICS_API_KEY",
    "TOGETHER_API_KEY",
)
_COST_SECRET_PATTERNS = (
    (
        re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|key|token)?\s*)[^\s,;]+"),
        r"\1[redacted]",
    ),
    (
        re.compile(r"(?i)\b(bearer|key|token)\s+[A-Za-z0-9._~+/=-]{8,}"),
        r"\1 [redacted]",
    ),
    (
        re.compile(r"(?i)\b(api[_-]?key|token|secret)(\s*[:=]\s*)[^\s,;]+"),
        r"\1\2[redacted]",
    ),
)
_MKD_TEXT = {
    "en": {
        "transcription_metadata": "Transcription Metadata",
        "overview": "Overview",
        "metric": "Metric",
        "value": "Value",
        "duration_ms": "Duration (ms)",
        "speaker_count": "Speaker count",
        "speech_coverage": "Speech coverage",
        "word_count": "Word count",
        "character_count": "Character count",
        "speaker_details": "Speaker Details",
        "no_speaker_details": "No speaker details are available for this transcription.",
        "speaker": "Speaker",
        "spoken_ms": "Spoken (ms)",
        "audio_share": "Audio Share",
        "first_speech": "First Speech",
        "last_speech": "Last Speech",
        "words": "Words",
        "characters": "Characters",
        "words_per_min": "Words/Min",
        "characters_per_min": "Characters/Min",
        "notes": "Notes",
        "note_segment_times": "Segment times are exported in `HH:MM:SS`.",
        "note_duration": "Duration and spoken times are stored in milliseconds.",
        "diarized_transcription": "Diarized Transcription",
        "segment_heading": "Segment {segment_number} · {speaker_label}",
        "time_label": "Time",
        "no_transcription_text": "_No transcription text available._",
    },
    "zh": {
        "transcription_metadata": "转录元数据",
        "overview": "概览",
        "metric": "指标",
        "value": "值",
        "duration_ms": "时长（毫秒）",
        "speaker_count": "说话人数",
        "speech_coverage": "语音覆盖率",
        "word_count": "词数",
        "character_count": "字符数",
        "speaker_details": "说话人详情",
        "no_speaker_details": "此转录暂无说话人详情。",
        "speaker": "说话人",
        "spoken_ms": "发言时长（毫秒）",
        "audio_share": "音频占比",
        "first_speech": "首次发言",
        "last_speech": "最后发言",
        "words": "词数",
        "characters": "字符数",
        "words_per_min": "每分钟词数",
        "characters_per_min": "每分钟字符数",
        "notes": "说明",
        "note_segment_times": "分段时间以 `HH:MM:SS` 导出。",
        "note_duration": "总时长和发言时长以毫秒存储。",
        "diarized_transcription": "分说话人转录",
        "segment_heading": "片段 {segment_number} · {speaker_label}",
        "time_label": "时间",
        "no_transcription_text": "_暂无转录文本。_",
    },
    "hi": {
        "transcription_metadata": "प्रतिलेखन मेटाडेटा",
        "overview": "सारांश",
        "metric": "मापदंड",
        "value": "मान",
        "duration_ms": "अवधि (मिलीसेकंड)",
        "speaker_count": "वक्ताओं की संख्या",
        "speech_coverage": "वाणी कवरेज",
        "word_count": "शब्द संख्या",
        "character_count": "अक्षर संख्या",
        "speaker_details": "वक्ता विवरण",
        "no_speaker_details": "इस प्रतिलेखन के लिए वक्ता विवरण उपलब्ध नहीं हैं।",
        "speaker": "वक्ता",
        "spoken_ms": "बोला गया समय (मिलीसेकंड)",
        "audio_share": "ऑडियो हिस्सा",
        "first_speech": "पहला वक्तव्य",
        "last_speech": "अंतिम वक्तव्य",
        "words": "शब्द",
        "characters": "अक्षर",
        "words_per_min": "शब्द/मिनट",
        "characters_per_min": "अक्षर/मिनट",
        "notes": "नोट्स",
        "note_segment_times": "सेगमेंट समय `HH:MM:SS` में निर्यात किए जाते हैं।",
        "note_duration": "अवधि और बोलने का समय मिलीसेकंड में संग्रहीत है।",
        "diarized_transcription": "स्पीकर-आधारित प्रतिलेखन",
        "segment_heading": "खंड {segment_number} · {speaker_label}",
        "time_label": "समय",
        "no_transcription_text": "_कोई प्रतिलेखन पाठ उपलब्ध नहीं है।_",
    },
    "es": {
        "transcription_metadata": "Metadatos de la Transcripción",
        "overview": "Resumen",
        "metric": "Métrica",
        "value": "Valor",
        "duration_ms": "Duración (ms)",
        "speaker_count": "Cantidad de hablantes",
        "speech_coverage": "Cobertura de voz",
        "word_count": "Cantidad de palabras",
        "character_count": "Cantidad de caracteres",
        "speaker_details": "Detalles de Hablantes",
        "no_speaker_details": "No hay detalles de hablantes disponibles para esta transcripción.",
        "speaker": "Hablante",
        "spoken_ms": "Tiempo hablado (ms)",
        "audio_share": "Porcentaje del audio",
        "first_speech": "Primera intervención",
        "last_speech": "Última intervención",
        "words": "Palabras",
        "characters": "Caracteres",
        "words_per_min": "Palabras/Min",
        "characters_per_min": "Caracteres/Min",
        "notes": "Notas",
        "note_segment_times": "Los tiempos de los segmentos se exportan en `HH:MM:SS`.",
        "note_duration": "La duración y los tiempos hablados se almacenan en milisegundos.",
        "diarized_transcription": "Transcripción Diarizada",
        "segment_heading": "Segmento {segment_number} · {speaker_label}",
        "time_label": "Tiempo",
        "no_transcription_text": "_No hay texto de transcripción disponible._",
    },
    "fr": {
        "transcription_metadata": "Métadonnées de Transcription",
        "overview": "Vue d’ensemble",
        "metric": "Mesure",
        "value": "Valeur",
        "duration_ms": "Durée (ms)",
        "speaker_count": "Nombre de locuteurs",
        "speech_coverage": "Couverture de parole",
        "word_count": "Nombre de mots",
        "character_count": "Nombre de caractères",
        "speaker_details": "Détails des Locuteurs",
        "no_speaker_details": "Aucun détail de locuteur n’est disponible pour cette transcription.",
        "speaker": "Locuteur",
        "spoken_ms": "Temps parlé (ms)",
        "audio_share": "Part de l’audio",
        "first_speech": "Première prise de parole",
        "last_speech": "Dernière prise de parole",
        "words": "Mots",
        "characters": "Caractères",
        "words_per_min": "Mots/Min",
        "characters_per_min": "Caractères/Min",
        "notes": "Notes",
        "note_segment_times": "Les temps des segments sont exportés en `HH:MM:SS`.",
        "note_duration": "La durée et les temps parlés sont stockés en millisecondes.",
        "diarized_transcription": "Transcription Diarisée",
        "segment_heading": "Segment {segment_number} · {speaker_label}",
        "time_label": "Temps",
        "no_transcription_text": "_Aucun texte de transcription disponible._",
    },
    "ar": {
        "transcription_metadata": "بيانات النسخ",
        "overview": "نظرة عامة",
        "metric": "المؤشر",
        "value": "القيمة",
        "duration_ms": "المدة (مللي ثانية)",
        "speaker_count": "عدد المتحدثين",
        "speech_coverage": "نسبة تغطية الكلام",
        "word_count": "عدد الكلمات",
        "character_count": "عدد الأحرف",
        "speaker_details": "تفاصيل المتحدثين",
        "no_speaker_details": "لا توجد تفاصيل متحدثين متاحة لهذا النسخ.",
        "speaker": "المتحدث",
        "spoken_ms": "مدة الكلام (مللي ثانية)",
        "audio_share": "حصة الصوت",
        "first_speech": "أول كلام",
        "last_speech": "آخر كلام",
        "words": "الكلمات",
        "characters": "الأحرف",
        "words_per_min": "كلمات/دقيقة",
        "characters_per_min": "أحرف/دقيقة",
        "notes": "ملاحظات",
        "note_segment_times": "يتم تصدير أزمنة المقاطع بصيغة `HH:MM:SS`.",
        "note_duration": "يتم تخزين المدة وأزمنة الكلام بالمللي ثانية.",
        "diarized_transcription": "النسخ حسب المتحدث",
        "segment_heading": "مقطع {segment_number} · {speaker_label}",
        "time_label": "الوقت",
        "no_transcription_text": "_لا يوجد نص نسخ متاح._",
    },
    "bn": {
        "transcription_metadata": "ট্রান্সক্রিপশন মেটাডেটা",
        "overview": "সারসংক্ষেপ",
        "metric": "মেট্রিক",
        "value": "মান",
        "duration_ms": "সময়কাল (মিলিসেকেন্ড)",
        "speaker_count": "স্পিকারের সংখ্যা",
        "speech_coverage": "বক্তব্য কভারেজ",
        "word_count": "শব্দ সংখ্যা",
        "character_count": "অক্ষর সংখ্যা",
        "speaker_details": "স্পিকার বিবরণ",
        "no_speaker_details": "এই ট্রান্সক্রিপশনের জন্য কোনো স্পিকার বিবরণ নেই।",
        "speaker": "স্পিকার",
        "spoken_ms": "বলার সময় (মিলিসেকেন্ড)",
        "audio_share": "অডিও অংশ",
        "first_speech": "প্রথম বক্তব্য",
        "last_speech": "শেষ বক্তব্য",
        "words": "শব্দ",
        "characters": "অক্ষর",
        "words_per_min": "শব্দ/মিনিট",
        "characters_per_min": "অক্ষর/মিনিট",
        "notes": "নোট",
        "note_segment_times": "সেগমেন্ট সময় `HH:MM:SS` ফরম্যাটে এক্সপোর্ট করা হয়।",
        "note_duration": "মোট সময় ও বলার সময় মিলিসেকেন্ডে সংরক্ষিত থাকে।",
        "diarized_transcription": "স্পিকারভিত্তিক ট্রান্সক্রিপশন",
        "segment_heading": "সেগমেন্ট {segment_number} · {speaker_label}",
        "time_label": "সময়",
        "no_transcription_text": "_কোনো ট্রান্সক্রিপশন টেক্সট নেই।_",
    },
    "pt": {
        "transcription_metadata": "Metadados da Transcrição",
        "overview": "Visão Geral",
        "metric": "Métrica",
        "value": "Valor",
        "duration_ms": "Duração (ms)",
        "speaker_count": "Quantidade de speakers",
        "speech_coverage": "Cobertura de fala",
        "word_count": "Quantidade de palavras",
        "character_count": "Quantidade de caracteres",
        "speaker_details": "Detalhes dos Speakers",
        "no_speaker_details": "Não há detalhes de speakers disponíveis para esta transcrição.",
        "speaker": "Speaker",
        "spoken_ms": "Falado (ms)",
        "audio_share": "Participação no áudio",
        "first_speech": "Primeira fala",
        "last_speech": "Última fala",
        "words": "Palavras",
        "characters": "Caracteres",
        "words_per_min": "Palavras/Min",
        "characters_per_min": "Caracteres/Min",
        "notes": "Notas",
        "note_segment_times": "Os tempos dos segmentos são exportados em `HH:MM:SS`.",
        "note_duration": "A duração e os tempos falados são armazenados em milissegundos.",
        "diarized_transcription": "Transcrição Diarizada",
        "segment_heading": "Segmento {segment_number} · {speaker_label}",
        "time_label": "Tempo",
        "no_transcription_text": "_Nenhum texto de transcrição disponível._",
    },
    "ru": {
        "transcription_metadata": "Метаданные Транскрипции",
        "overview": "Обзор",
        "metric": "Метрика",
        "value": "Значение",
        "duration_ms": "Длительность (мс)",
        "speaker_count": "Количество спикеров",
        "speech_coverage": "Покрытие речи",
        "word_count": "Количество слов",
        "character_count": "Количество символов",
        "speaker_details": "Детали Спикеров",
        "no_speaker_details": "Для этой транскрипции нет сведений о спикерах.",
        "speaker": "Спикер",
        "spoken_ms": "Речь (мс)",
        "audio_share": "Доля аудио",
        "first_speech": "Первая речь",
        "last_speech": "Последняя речь",
        "words": "Слова",
        "characters": "Символы",
        "words_per_min": "Слов/Мин",
        "characters_per_min": "Символов/Мин",
        "notes": "Примечания",
        "note_segment_times": "Время сегментов экспортируется в формате `HH:MM:SS`.",
        "note_duration": "Длительность и время речи хранятся в миллисекундах.",
        "diarized_transcription": "Диаризованная Транскрипция",
        "segment_heading": "Сегмент {segment_number} · {speaker_label}",
        "time_label": "Время",
        "no_transcription_text": "_Текст транскрипции недоступен._",
    },
    "ur": {
        "transcription_metadata": "ٹرانسکرپشن میٹاڈیٹا",
        "overview": "جائزہ",
        "metric": "میٹرک",
        "value": "قدر",
        "duration_ms": "دورانیہ (ملی سیکنڈ)",
        "speaker_count": "اسپیکرز کی تعداد",
        "speech_coverage": "گفتار کی کوریج",
        "word_count": "الفاظ کی تعداد",
        "character_count": "حروف کی تعداد",
        "speaker_details": "اسپیکر کی تفصیلات",
        "no_speaker_details": "اس ٹرانسکرپشن کے لیے اسپیکر کی تفصیلات دستیاب نہیں ہیں۔",
        "speaker": "اسپیکر",
        "spoken_ms": "بولنے کا وقت (ملی سیکنڈ)",
        "audio_share": "آڈیو حصہ",
        "first_speech": "پہلی گفتگو",
        "last_speech": "آخری گفتگو",
        "words": "الفاظ",
        "characters": "حروف",
        "words_per_min": "الفاظ/منٹ",
        "characters_per_min": "حروف/منٹ",
        "notes": "نوٹس",
        "note_segment_times": "سیگمنٹ کے اوقات `HH:MM:SS` میں ایکسپورٹ کیے جاتے ہیں۔",
        "note_duration": "دورانیہ اور بولنے کے اوقات ملی سیکنڈ میں محفوظ ہوتے ہیں۔",
        "diarized_transcription": "اسپیکر کے لحاظ سے ٹرانسکرپشن",
        "segment_heading": "حصہ {segment_number} · {speaker_label}",
        "time_label": "وقت",
        "no_transcription_text": "_کوئی ٹرانسکرپشن متن دستیاب نہیں ہے۔_",
    },
}


def _safe_float(value, default=0.0):
    """Converts a value to float and falls back when conversion fails."""
    try:
        return float(value)
    except Exception:
        return default


def _clean_text(text):
    """Normalizes repeated whitespace inside text."""
    return " ".join(str(text or "").strip().split())


def _sanitize_cost_lookup_error(error):
    """Returns a compact, non-secret cost lookup error message."""
    if error is None:
        return None
    cleaned = _clean_text(error)
    if not cleaned:
        return None
    for env_var in _COST_SECRET_ENV_VARS:
        secret_value = str(os.getenv(env_var) or "").strip()
        if len(secret_value) >= 6:
            cleaned = cleaned.replace(secret_value, "[redacted]")
    for pattern, replacement in _COST_SECRET_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned[:500]


def _normalize_cost_source(cost_source):
    """Returns one supported public cost source value."""
    normalized = _clean_text(cost_source)
    if normalized in _VALID_COST_SOURCES:
        return normalized
    return "unavailable"


def _normalize_cost_usd(cost_usd):
    """Preserves unknown cost as None and validates known numeric costs."""
    if cost_usd is None:
        return None
    return float(cost_usd)


def _ensure_payload(transcription_payload):
    """Validates that the input payload is a raw transcription dictionary."""
    if not isinstance(transcription_payload, dict):
        raise TypeError("transcription_payload must be a raw transcription dictionary.")
    return transcription_payload


def _compact_value(value):
    """Recursively removes empty values while preserving valid scalars."""
    if isinstance(value, dict):
        compacted = {}
        for key, item in value.items():
            compacted_item = _compact_value(item)
            if compacted_item in (None, "", [], {}):
                continue
            compacted[key] = compacted_item
        return compacted

    if isinstance(value, list | tuple):
        compacted_items = []
        for item in value:
            compacted_item = _compact_value(item)
            if compacted_item in (None, "", [], {}):
                continue
            compacted_items.append(compacted_item)
        return compacted_items

    if isinstance(value, str):
        return str(value).strip()

    return value


def _get_transcription_info(transcription_payload):
    """Returns transcription metadata from the payload."""
    payload = _ensure_payload(transcription_payload)
    info = payload.get("transcription_info")
    if isinstance(info, dict):
        return _compact_value(dict(info))

    result_metadata = (payload.get("result") or {}).get("metadata") or {}
    result_payload = payload.get("result") or {}
    response_root = result_payload.get("results", {}) or {}
    channels = response_root.get("channels", []) or [{}]
    alternative = (channels[0].get("alternatives", []) or [{}])[0]
    return _compact_value(
        {
            "provider": "deepgram",
            "language": channels[0].get("detected_language"),
            "text": alternative.get("transcript"),
            "provider_metadata": {
                "warnings": result_metadata.get("warnings"),
                "model_info": result_metadata.get("model_info"),
                "models": result_metadata.get("models"),
                "transaction_key": result_metadata.get("transaction_key"),
                "created": result_metadata.get("created"),
                "sha256": result_metadata.get("sha256"),
            },
            "audio_duration_seconds": _safe_float(result_metadata.get("duration"), 0.0),
        }
    )


def build_raw_transcription_payload(
    *,
    provider,
    model,
    audio_duration_seconds,
    language=None,
    language_confidence=None,
    text=None,
    words=None,
    utterances=None,
    provider_metadata=None,
    result=None,
):
    """Builds the raw multi-provider payload consumed by transcription post-processing."""
    payload = {
        "transcription_info": _compact_value(
            {
                "provider": _clean_text(provider),
                "model": _clean_text(model),
                "language": _clean_text(language),
                "language_confidence": _safe_float(language_confidence, None) if language_confidence is not None else None,
                "text": str(text).strip() if text is not None else None,
                "audio_duration_seconds": round(max(0.0, _safe_float(audio_duration_seconds, 0.0)), 6),
                "provider_metadata": _compact_value(provider_metadata or {}),
            }
        )
    }

    if words:
        payload["words"] = list(words)
    if utterances:
        payload["utterances"] = list(utterances)
    if isinstance(result, dict):
        payload["result"] = result

    return payload


def _get_audio_duration_seconds(transcription_payload):
    """Returns the best available audio duration in seconds."""
    info = _get_transcription_info(transcription_payload)
    duration_seconds = _safe_float(info.get("audio_duration_seconds"), 0.0)
    if duration_seconds > 0:
        return duration_seconds

    payload = _ensure_payload(transcription_payload)
    result_metadata = (payload.get("result") or {}).get("metadata") or {}
    duration_seconds = _safe_float(result_metadata.get("duration"), 0.0)
    if duration_seconds > 0:
        return duration_seconds

    utterances = _normalize_utterances(payload)
    if utterances:
        return max(_safe_float(utterance.get("end"), 0.0) for utterance in utterances)

    words = _normalize_words(payload)
    if words:
        return max(_safe_float(word.get("end"), 0.0) for word in words)

    return 0.0


def _get_language_code(transcription_payload):
    """Returns the best available language code from the payload."""
    info = _get_transcription_info(transcription_payload)
    language = _clean_text(info.get("language"))
    if language:
        return language

    payload = _ensure_payload(transcription_payload)
    result_payload = payload.get("result") or {}
    response_root = result_payload.get("results", {}) or {}
    channels = response_root.get("channels", []) or [{}]
    return _clean_text(channels[0].get("detected_language"))


def _get_transcript_text(transcription_payload):
    """Returns the best available transcript text from the payload."""
    info = _get_transcription_info(transcription_payload)
    transcript_text = str(info.get("text") or "").strip()
    if transcript_text:
        return transcript_text

    utterances = _normalize_utterances(transcription_payload)
    if utterances:
        return _clean_text(" ".join(utterance.get("text", "") for utterance in utterances))

    words = _normalize_words(transcription_payload)
    if words:
        return _words_to_text(words)

    payload = _ensure_payload(transcription_payload)
    result_payload = payload.get("result") or {}
    response_root = result_payload.get("results", {}) or {}
    channels = response_root.get("channels", []) or [{}]
    alternative = (channels[0].get("alternatives", []) or [{}])[0]
    return _clean_text(alternative.get("transcript"))


def _normalize_word_payload(word_payload, default_speaker=0):
    """Normalizes a word entry from the transcription payload."""
    text = _clean_text(word_payload.get("text") or word_payload.get("punctuated_word") or word_payload.get("word"))
    if not text:
        return None

    start = _safe_float(word_payload.get("start"), 0.0)
    end = _safe_float(word_payload.get("end"), start)
    if end < start:
        end = start

    speaker = word_payload.get("speaker")
    if speaker is None:
        speaker = default_speaker

    return {
        "start": start,
        "end": end,
        "text": text,
        "speaker": speaker,
    }


def _build_normalized_utterance(utterance_payload, default_speaker=0):
    """Normalizes an utterance-like payload into the internal structure."""
    speaker = utterance_payload.get("speaker", default_speaker)
    words = []
    for word_payload in utterance_payload.get("words") or []:
        normalized_word = _normalize_word_payload(word_payload, default_speaker=speaker)
        if normalized_word:
            words.append(normalized_word)

    text = _clean_text(utterance_payload.get("text") or utterance_payload.get("transcript"))
    if words:
        text = _clean_text(" ".join(word["text"] for word in words))
    if not text:
        return None

    start = _safe_float(utterance_payload.get("start"), 0.0)
    end = _safe_float(utterance_payload.get("end"), start)
    if words:
        start = min(start, words[0]["start"])
        end = max(end, words[-1]["end"])
    if end < start:
        end = start

    return {
        "start": round(start, 6),
        "end": round(end, 6),
        "text": text,
        "speaker": speaker,
        "words": words,
    }


def _normalize_words(transcription_payload):
    """Returns normalized payload words sorted by time."""
    payload = _ensure_payload(transcription_payload)
    words = []

    for word_payload in payload.get("words") or []:
        normalized_word = _normalize_word_payload(word_payload, default_speaker=0)
        if normalized_word:
            words.append(normalized_word)

    if words:
        words.sort(key=lambda item: (item["start"], item["end"]))
        return words

    result_payload = payload.get("result") or {}
    response_root = result_payload.get("results", {}) or {}
    utterances = response_root.get("utterances", []) or []
    for utterance_payload in utterances:
        speaker = utterance_payload.get("speaker", 0)
        for word_payload in utterance_payload.get("words") or []:
            normalized_word = _normalize_word_payload(word_payload, default_speaker=speaker)
            if normalized_word:
                words.append(normalized_word)

    if words:
        words.sort(key=lambda item: (item["start"], item["end"]))
        return words

    channels = response_root.get("channels", []) or [{}]
    alternative = (channels[0].get("alternatives", []) or [{}])[0]
    for word_payload in alternative.get("words", []) or []:
        normalized_word = _normalize_word_payload(word_payload, default_speaker=0)
        if normalized_word:
            words.append(normalized_word)

    words.sort(key=lambda item: (item["start"], item["end"]))
    return words


def _normalize_utterances(transcription_payload):
    """Returns normalized payload utterances sorted by time."""
    payload = _ensure_payload(transcription_payload)
    utterances = []

    for utterance_payload in payload.get("utterances") or []:
        normalized_utterance = _build_normalized_utterance(utterance_payload, default_speaker=0)
        if normalized_utterance:
            utterances.append(normalized_utterance)

    if utterances:
        utterances.sort(key=lambda item: (item["start"], item["end"]))
        return utterances

    result_payload = payload.get("result") or {}
    response_root = result_payload.get("results", {}) or {}
    for utterance_payload in response_root.get("utterances", []) or []:
        normalized_utterance = _build_normalized_utterance(utterance_payload, default_speaker=0)
        if normalized_utterance:
            utterances.append(normalized_utterance)

    if utterances:
        utterances.sort(key=lambda item: (item["start"], item["end"]))
        return utterances

    channels = response_root.get("channels", []) or [{}]
    alternative = (channels[0].get("alternatives", []) or [{}])[0]
    fallback_utterance = _build_normalized_utterance(
        {
            "start": 0.0,
            "end": _safe_float((result_payload.get("metadata") or {}).get("duration"), 0.0),
            "transcript": alternative.get("transcript"),
            "speaker": 0,
            "words": alternative.get("words", []) or [],
        },
        default_speaker=0,
    )
    if fallback_utterance:
        utterances.append(fallback_utterance)

    utterances.sort(key=lambda item: (item["start"], item["end"]))
    return utterances


def _deduplicate_words(words):
    """Removes near-duplicate normalized words."""
    if not words:
        return []

    ordered_words = sorted(words, key=lambda item: (_safe_float(item.get("start"), 0.0), _safe_float(item.get("end"), 0.0)))
    deduplicated_words = []
    for word in ordered_words:
        text = _clean_text(word.get("text"))
        if not text:
            continue

        start = _safe_float(word.get("start"), 0.0)
        end = _safe_float(word.get("end"), start)
        if end < start:
            end = start

        candidate_word = {
            "start": start,
            "end": end,
            "text": text,
            "speaker_raw": word.get("speaker_raw", word.get("speaker", 0)),
        }
        if deduplicated_words:
            previous_word = deduplicated_words[-1]
            same_text = previous_word["text"].lower() == candidate_word["text"].lower()
            close_time = abs(previous_word["start"] - candidate_word["start"]) <= 0.03 and abs(previous_word["end"] - candidate_word["end"]) <= 0.03
            if same_text and close_time:
                continue
        deduplicated_words.append(candidate_word)

    return deduplicated_words


def _words_to_text(words):
    """Joins normalized words into one cleaned sentence."""
    if not words:
        return ""
    return _clean_text(" ".join(_clean_text(word.get("text")) for word in words if _clean_text(word.get("text"))))


def _segment_text(segment):
    """Returns the best text representation available for a raw segment."""
    text_from_words = _words_to_text(segment.get("words") or [])
    if text_from_words:
        return text_from_words
    return _clean_text(segment.get("text"))


def _normalize_segment(segment):
    """Normalizes a raw segment dictionary."""
    start = _safe_float(segment.get("start"), 0.0)
    end = _safe_float(segment.get("end"), start)
    if end < start:
        end = start

    words = _deduplicate_words(segment.get("words") or [])
    text = _words_to_text(words) or _clean_text(segment.get("text"))
    if not text:
        return None

    return {
        "speaker_raw": segment.get("speaker_raw", segment.get("speaker", 0)),
        "start": start,
        "end": end,
        "text": text,
        "words": words,
    }


def _build_raw_segments(transcription_payload):
    """Builds diarization-aware raw segments from normalized utterances or words."""
    utterances = _normalize_utterances(transcription_payload)
    raw_segments = []

    for utterance in utterances:
        speaker = utterance.get("speaker", 0)
        words = []
        for word in utterance.get("words") or []:
            words.append(
                {
                    "start": word["start"],
                    "end": word["end"],
                    "text": word["text"],
                    "speaker_raw": word.get("speaker", speaker),
                }
            )
        words = _deduplicate_words(words)

        text = _words_to_text(words) or _clean_text(utterance.get("text"))
        if not text:
            continue

        start = _safe_float(utterance.get("start"), 0.0)
        end = _safe_float(utterance.get("end"), start)
        if words:
            start = min(start, words[0]["start"])
            end = max(end, words[-1]["end"])
        if end < start:
            end = start

        raw_segments.append(
            {
                "speaker_raw": speaker,
                "start": start,
                "end": end,
                "text": text,
                "words": words,
            }
        )

    if raw_segments:
        return raw_segments

    words = _normalize_words(transcription_payload)
    current_segment = None
    for word in words:
        speaker = word.get("speaker", 0)
        if (
            current_segment
            and current_segment["speaker_raw"] == speaker
            and (word["start"] - current_segment["end"]) <= _SEGMENT_JOIN_GAP_SECONDS
        ):
            current_segment["end"] = max(current_segment["end"], word["end"])
            current_segment["words"].append(
                {
                    "start": word["start"],
                    "end": word["end"],
                    "text": word["text"],
                    "speaker_raw": speaker,
                }
            )
            current_segment["text"] = _words_to_text(current_segment["words"])
        else:
            if current_segment:
                current_segment["words"] = _deduplicate_words(current_segment.get("words") or [])
                current_segment["text"] = _words_to_text(current_segment["words"]) or _clean_text(current_segment.get("text"))
                raw_segments.append(current_segment)
            current_segment = {
                "speaker_raw": speaker,
                "start": word["start"],
                "end": word["end"],
                "text": word["text"],
                "words": [
                    {
                        "start": word["start"],
                        "end": word["end"],
                        "text": word["text"],
                        "speaker_raw": speaker,
                    }
                ],
            }

    if current_segment:
        current_segment["words"] = _deduplicate_words(current_segment.get("words") or [])
        current_segment["text"] = _words_to_text(current_segment["words"]) or _clean_text(current_segment.get("text"))
        raw_segments.append(current_segment)

    if raw_segments:
        return raw_segments

    payload = _ensure_payload(transcription_payload)
    result_payload = payload.get("result") or {}
    response_root = result_payload.get("results", {}) or {}
    channels = response_root.get("channels", []) or [{}]
    alternative = (channels[0].get("alternatives", []) or [{}])[0]
    transcript = _clean_text(alternative.get("transcript"))
    if transcript:
        duration_seconds = _get_audio_duration_seconds(transcription_payload)
        return [
            {
                "speaker_raw": 0,
                "start": 0.0,
                "end": duration_seconds,
                "text": transcript,
                "words": [],
            }
        ]

    return []


def _split_text_into_parts(text, parts_count):
    """Splits text into balanced textual parts."""
    text = _clean_text(text)
    parts_count = max(1, int(parts_count))
    if parts_count == 1:
        return [text]
    if not text:
        return [""] * parts_count

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?;:])\s+", text) if sentence.strip()]
    if len(sentences) >= parts_count:
        parts = []
        total_sentences = len(sentences)
        for part_index in range(parts_count):
            start_index = int((part_index * total_sentences) / parts_count)
            end_index = int(((part_index + 1) * total_sentences) / parts_count)
            parts.append(_clean_text(" ".join(sentences[start_index:end_index])))
        return parts

    tokens = text.split()
    if not tokens:
        return [""] * parts_count

    parts = []
    total_tokens = len(tokens)
    for part_index in range(parts_count):
        start_index = int((part_index * total_tokens) / parts_count)
        end_index = int(((part_index + 1) * total_tokens) / parts_count)
        parts.append(_clean_text(" ".join(tokens[start_index:end_index])))
    return parts


def _word_end(word):
    """Returns the end time of a normalized word."""
    start = _safe_float(word.get("start"), 0.0)
    end = _safe_float(word.get("end"), start)
    if end < start:
        end = start
    return end


def _has_strong_punctuation(text):
    """Returns whether text contains a strong split punctuation mark."""
    return bool(_STRONG_PUNCTUATION_RE.search(str(text or "")))


def _has_comma(text):
    """Returns whether text contains a comma split candidate."""
    return bool(_COMMA_RE.search(str(text or "")))


def _collect_indices_in_interval(words, start_index, end_index, start_time, end_time, reverse=False):
    """Collects word indices whose end time falls inside the interval."""
    if end_index < start_index:
        return []

    indices = []
    for word_index in range(start_index, end_index + 1):
        word_time = _word_end(words[word_index])
        if start_time <= word_time <= end_time:
            indices.append((word_time, word_index))

    indices.sort(key=lambda item: item[0], reverse=reverse)
    return [word_index for _, word_index in indices]


def _find_closest_index(words, start_index, end_index, target_time):
    """Returns the index whose end time is closest to the target."""
    best_index = start_index
    best_delta = None
    for word_index in range(start_index, end_index + 1):
        delta = abs(_word_end(words[word_index]) - target_time)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_index = word_index
    return best_index


def _choose_split_index(words, start_index, end_index, target_time, window_seconds=_SPLIT_WINDOW_SECONDS):
    """Chooses the best split point around the target time."""
    if end_index <= start_index:
        return start_index

    backward_indices = _collect_indices_in_interval(
        words,
        start_index,
        end_index,
        target_time - window_seconds,
        target_time,
        reverse=True,
    )
    for word_index in backward_indices:
        if _has_strong_punctuation(words[word_index].get("text")):
            return word_index

    forward_indices = _collect_indices_in_interval(
        words,
        start_index,
        end_index,
        target_time,
        target_time + window_seconds,
        reverse=False,
    )
    for word_index in forward_indices:
        if _has_strong_punctuation(words[word_index].get("text")):
            return word_index

    for word_index in backward_indices:
        if _has_comma(words[word_index].get("text")):
            return word_index

    for word_index in forward_indices:
        if _has_comma(words[word_index].get("text")):
            return word_index

    return _find_closest_index(words, start_index, end_index, target_time)


def _force_split_segment(segment):
    """Force-splits a segment when its duration is still above the hard limit."""
    duration_seconds = max(0.0, _safe_float(segment.get("end"), 0.0) - _safe_float(segment.get("start"), 0.0))
    if duration_seconds <= _SEGMENT_MAX_SECONDS + 1e-6:
        return [segment]

    parts_count = max(2, int(math.ceil(duration_seconds / _SEGMENT_MAX_SECONDS)))
    texts = _split_text_into_parts(_segment_text(segment), parts_count)
    start = _safe_float(segment.get("start"), 0.0)
    end = _safe_float(segment.get("end"), start)
    if end < start:
        end = start

    split_segments = []
    for part_index in range(parts_count):
        part_start = start + ((end - start) * part_index / float(parts_count))
        part_end = start + ((end - start) * (part_index + 1) / float(parts_count))
        if part_index == parts_count - 1:
            part_end = end
        if part_end < part_start:
            part_end = part_start
        split_segments.append(
            {
                "speaker_raw": segment.get("speaker_raw", 0),
                "start": part_start,
                "end": part_end,
                "text": _clean_text(texts[part_index] if part_index < len(texts) else ""),
                "words": [],
            }
        )

    return split_segments


def _split_segment_without_words(segment):
    """Splits a segment by time when word-level timing is not available."""
    duration_seconds = max(0.0, _safe_float(segment.get("end"), 0.0) - _safe_float(segment.get("start"), 0.0))
    if duration_seconds <= _SEGMENT_MAX_SECONDS + 1e-6:
        return [segment]

    parts_count = max(2, int(math.ceil(duration_seconds / _SEGMENT_TARGET_SECONDS)))
    texts = _split_text_into_parts(_segment_text(segment), parts_count)
    start = _safe_float(segment.get("start"), 0.0)
    end = _safe_float(segment.get("end"), start)
    if end < start:
        end = start

    split_segments = []
    for part_index in range(parts_count):
        part_start = start + ((end - start) * part_index / float(parts_count))
        part_end = start + ((end - start) * (part_index + 1) / float(parts_count))
        if part_index == parts_count - 1:
            part_end = end
        if part_end < part_start:
            part_end = part_start
        split_segments.append(
            {
                "speaker_raw": segment.get("speaker_raw", 0),
                "start": part_start,
                "end": part_end,
                "text": _clean_text(texts[part_index] if part_index < len(texts) else ""),
                "words": [],
            }
        )

    final_segments = []
    for split_segment in split_segments:
        if (split_segment["end"] - split_segment["start"]) > _SEGMENT_MAX_SECONDS + 1e-6:
            final_segments.extend(_force_split_segment(split_segment))
        else:
            final_segments.append(split_segment)
    return final_segments


def _split_segment_with_words(segment):
    """Splits a long segment using word boundaries and punctuation clues."""
    duration_seconds = max(0.0, _safe_float(segment.get("end"), 0.0) - _safe_float(segment.get("start"), 0.0))
    if duration_seconds <= _SEGMENT_MAX_SECONDS + 1e-6:
        return [segment]

    words = _deduplicate_words(segment.get("words") or [])
    if len(words) < 2:
        return _split_segment_without_words(segment)

    parts_count = max(2, int(math.ceil(duration_seconds / _SEGMENT_TARGET_SECONDS)))
    split_segments = []
    current_start_index = 0
    remaining_parts = parts_count
    current_start_time = max(_safe_float(segment.get("start"), 0.0), _safe_float(words[0].get("start"), 0.0))

    while remaining_parts > 1 and current_start_index < len(words) - 1:
        max_index = len(words) - remaining_parts
        if max_index < current_start_index:
            break

        remaining_duration = max(0.0, _safe_float(segment.get("end"), current_start_time) - current_start_time)
        target_time = current_start_time + (remaining_duration / float(remaining_parts))
        split_index = _choose_split_index(words, current_start_index, max_index, target_time)
        if split_index < current_start_index:
            split_index = current_start_index

        block_words = words[current_start_index : split_index + 1]
        if not block_words:
            break

        block_start = _safe_float(segment.get("start"), 0.0) if not split_segments else max(
            current_start_time,
            _safe_float(block_words[0].get("start"), current_start_time),
        )
        block_end = _safe_float(block_words[-1].get("end"), _safe_float(block_words[-1].get("start"), block_start))
        if block_end < block_start:
            block_end = block_start

        split_segments.append(
            {
                "speaker_raw": segment.get("speaker_raw", 0),
                "start": block_start,
                "end": block_end,
                "text": _words_to_text(block_words),
                "words": block_words,
            }
        )

        current_start_index = split_index + 1
        remaining_parts -= 1
        if current_start_index >= len(words):
            break
        next_start = _safe_float(words[current_start_index].get("start"), block_end)
        current_start_time = max(block_end, next_start)

    if current_start_index < len(words):
        block_words = words[current_start_index:]
        block_start = _safe_float(segment.get("start"), 0.0) if not split_segments else max(
            current_start_time,
            _safe_float(block_words[0].get("start"), current_start_time),
        )
        block_end = max(block_start, _safe_float(segment.get("end"), block_start))
        split_segments.append(
            {
                "speaker_raw": segment.get("speaker_raw", 0),
                "start": block_start,
                "end": block_end,
                "text": _words_to_text(block_words) or _segment_text(segment),
                "words": block_words,
            }
        )

    if not split_segments:
        return _split_segment_without_words(segment)

    final_segments = []
    for split_segment in split_segments:
        if (split_segment["end"] - split_segment["start"]) > _SEGMENT_MAX_SECONDS + 1e-6:
            final_segments.extend(_force_split_segment(split_segment))
        else:
            final_segments.append(split_segment)
    return final_segments


def _merge_adjacent_segments(segments, max_duration=None):
    """Merges adjacent segments from the same speaker when appropriate."""
    if not segments:
        return []

    merged_segments = []
    for segment in segments:
        normalized_segment = _normalize_segment(segment)
        if not normalized_segment:
            continue

        if not merged_segments:
            merged_segments.append(normalized_segment)
            continue

        previous_segment = merged_segments[-1]
        same_speaker = str(previous_segment.get("speaker_raw")) == str(normalized_segment.get("speaker_raw"))
        close_in_time = (_safe_float(normalized_segment.get("start"), 0.0) - _safe_float(previous_segment.get("end"), 0.0)) <= _SEGMENT_JOIN_GAP_SECONDS
        can_merge = True

        if max_duration is not None:
            merged_duration = max(
                _safe_float(previous_segment.get("end"), 0.0),
                _safe_float(normalized_segment.get("end"), 0.0),
            ) - _safe_float(previous_segment.get("start"), 0.0)
            if merged_duration > (_safe_float(max_duration, _SEGMENT_MAX_SECONDS) + 1e-6):
                can_merge = False

        if same_speaker and close_in_time and can_merge:
            previous_segment["end"] = max(
                _safe_float(previous_segment.get("end"), 0.0),
                _safe_float(normalized_segment.get("end"), 0.0),
            )
            previous_segment["words"] = _deduplicate_words((previous_segment.get("words") or []) + (normalized_segment.get("words") or []))
            if previous_segment["words"]:
                previous_segment["text"] = _words_to_text(previous_segment["words"])
            else:
                previous_segment["text"] = _clean_text(f'{previous_segment.get("text", "")} {normalized_segment.get("text", "")}')
            continue

        merged_segments.append(normalized_segment)

    return merged_segments


def _split_long_segments(segments):
    """Splits only the segments that exceed the hard duration limit."""
    split_segments = []
    for segment in segments:
        normalized_segment = _normalize_segment(segment)
        if not normalized_segment:
            continue

        duration_seconds = _safe_float(normalized_segment.get("end"), 0.0) - _safe_float(normalized_segment.get("start"), 0.0)
        if duration_seconds > _SEGMENT_MAX_SECONDS + 1e-6:
            split_segments.extend(_split_segment_with_words(normalized_segment))
        else:
            split_segments.append(normalized_segment)
    return split_segments


def _to_hhmmss(total_seconds):
    """Formats whole seconds into `HH:MM:SS`."""
    total_seconds = max(0, int(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _integer_segment_bounds(start_seconds, end_seconds, max_duration=None):
    """Returns integer-safe segment bounds for exported speaker blocks."""
    start_integer = int(math.floor(max(0.0, start_seconds)))
    end_integer = int(math.ceil(max(start_seconds, end_seconds)))
    if end_integer < start_integer:
        end_integer = start_integer

    if max_duration is not None and (end_integer - start_integer) > int(max_duration):
        end_integer = start_integer + int(max_duration)

    return start_integer, end_integer


def _build_diarized_segment_records(transcription_payload):
    """Builds diarized speaker segments plus exact timing and word details."""
    raw_segments = _build_raw_segments(transcription_payload)
    if not raw_segments:
        return []

    ordered_segments = sorted(raw_segments, key=lambda item: (_safe_float(item.get("start"), 0.0), _safe_float(item.get("end"), 0.0)))
    merged_segments = _merge_adjacent_segments(ordered_segments)
    split_segments = _split_long_segments(merged_segments)
    final_base_segments = _merge_adjacent_segments(split_segments, max_duration=_SEGMENT_MAX_SECONDS)

    speaker_map = {}
    next_speaker_id = 0
    diarized_segments = []

    for segment in final_base_segments:
        duration_seconds = _safe_float(segment.get("end"), 0.0) - _safe_float(segment.get("start"), 0.0)
        candidate_segments = [segment]
        if duration_seconds > _SEGMENT_MAX_SECONDS + 1e-6:
            candidate_segments = _force_split_segment(segment)

        for candidate_segment in candidate_segments:
            speaker_key = str(candidate_segment.get("speaker_raw"))
            if speaker_key not in speaker_map:
                speaker_map[speaker_key] = next_speaker_id
                next_speaker_id += 1

            start_seconds = _safe_float(candidate_segment.get("start"), 0.0)
            end_seconds = _safe_float(candidate_segment.get("end"), start_seconds)
            if end_seconds < start_seconds:
                end_seconds = start_seconds

            speaker_id = speaker_map[speaker_key]
            segment_words = _deduplicate_words(candidate_segment.get("words") or [])
            start_integer, end_integer = _integer_segment_bounds(
                start_seconds,
                end_seconds,
                max_duration=int(_SEGMENT_MAX_SECONDS),
            )
            diarized_segments.append(
                {
                    "id": len(diarized_segments),
                    "speaker_id": speaker_id,
                    "speaker_raw": candidate_segment.get("speaker_raw"),
                    "start": start_seconds,
                    "end": end_seconds,
                    "start_time": _to_hhmmss(start_integer),
                    "end_time": _to_hhmmss(end_integer),
                    "text": _clean_text(_segment_text(candidate_segment)),
                    "words": segment_words,
                }
            )

    return diarized_segments


def _count_text_characters(text):
    """Counts non-whitespace characters inside arbitrary text."""
    return len("".join(character for character in str(text or "") if not character.isspace()))


def _count_characters_from_words(words):
    """Counts non-whitespace characters across normalized words."""
    return sum(_count_text_characters(word.get("text")) for word in (words or []))


def _format_percentage(value):
    """Clamps and rounds a percentage value."""
    try:
        percentage = float(value)
    except Exception:
        percentage = 0.0
    percentage = max(0.0, min(100.0, percentage))
    return round(percentage, 2)


def _normalize_language_mkd(language_mkd):
    """Validates the markdown language parameter."""
    if language_mkd is False:
        return False
    if language_mkd in _VALID_MKD_LANGUAGES:
        return language_mkd
    return False


def _translate(language, key, **kwargs):
    """Returns one localized markdown label."""
    language_key = language if language in _MKD_TEXT else "en"
    text = _MKD_TEXT[language_key][key]
    if kwargs:
        return text.format(**kwargs)
    return text


def _speaker_label(language, speaker_id):
    """Builds one localized speaker label."""
    return f'{_translate(language, "speaker")} {speaker_id}'


def _markdown_table_cell(value):
    """Formats one markdown table cell safely."""
    text = str(value if value is not None else "—")
    text = text.replace("\n", "<br>")
    return text.replace("|", r"\|")


def _build_markdown_table(headers, rows):
    """Builds a markdown table from headers and rows."""
    table_lines = [
        "| " + " | ".join(_markdown_table_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        table_lines.append("| " + " | ".join(_markdown_table_cell(cell) for cell in row) + " |")
    return "\n".join(table_lines)


def _assign_group_ids(words, max_window_seconds=_WORD_GROUP_MAX_WINDOW_SECONDS, max_words=_WORD_GROUP_MAX_WORDS):
    """Assigns visual group identifiers to normalized words."""
    if not words:
        return {}

    max_window_seconds = max(0.0, _safe_float(max_window_seconds, _WORD_GROUP_MAX_WINDOW_SECONDS))
    max_words = max(1, int(max_words or _WORD_GROUP_MAX_WORDS))

    group_ids = {}
    group_index = 0
    group_start = words[0]["start"]
    words_in_group = 0

    for word_index, word in enumerate(words):
        window_delta = word["end"] - group_start
        if word_index > 0 and (window_delta > max_window_seconds or words_in_group >= max_words):
            group_index += 1
            group_start = word["start"]
            words_in_group = 0

        group_ids[word_index] = group_index
        words_in_group += 1

    return group_ids


def _build_phrase_records(transcription_payload):
    """Builds implicit phrase records from normalized utterances."""
    utterances = _normalize_utterances(transcription_payload)
    phrase_records = []

    for phrase_id, utterance in enumerate(utterances):
        phrase_records.append(
            {
                "id": phrase_id,
                "start": _safe_float(utterance.get("start"), 0.0),
                "end": _safe_float(utterance.get("end"), 0.0),
                "speaker_raw": utterance.get("speaker", 0),
                "text": utterance.get("text"),
            }
        )

    if phrase_records:
        return phrase_records

    raw_segments = _build_raw_segments(transcription_payload)
    for phrase_id, segment in enumerate(raw_segments):
        phrase_records.append(
            {
                "id": phrase_id,
                "start": _safe_float(segment.get("start"), 0.0),
                "end": _safe_float(segment.get("end"), 0.0),
                "speaker_raw": segment.get("speaker_raw", 0),
                "text": segment.get("text"),
            }
        )

    return phrase_records


def _build_phrases_payload(phrase_records, segment_records):
    """Builds the top-level `phrases` dictionary."""
    speaker_map = {}
    for segment_record in segment_records or []:
        speaker_map[str(segment_record.get("speaker_raw"))] = int(segment_record.get("speaker_id", 0))

    phrases_payload = {}
    for phrase_record in phrase_records or []:
        start_seconds = _safe_float(phrase_record.get("start"), 0.0)
        end_seconds = _safe_float(phrase_record.get("end"), start_seconds)
        if end_seconds < start_seconds:
            end_seconds = start_seconds

        speaker_id = int(speaker_map.get(str(phrase_record.get("speaker_raw", 0)), 0))
        phrases_payload[int(phrase_record["id"])] = {
            "speaker_id": speaker_id,
            "start": int(round(start_seconds * 1000.0)),
            "end": int(round(end_seconds * 1000.0)),
            "text": _clean_text(phrase_record.get("text")),
        }

    return phrases_payload


def _find_record_id(records, start_seconds, end_seconds, speaker_id=None):
    """Finds the best matching phrase or segment id for one word."""
    if not records:
        return 0

    epsilon = 1e-6
    for record in records:
        same_speaker = speaker_id is None or int(record.get("speaker_id", speaker_id)) == int(speaker_id)
        if same_speaker and start_seconds >= (record["start"] - epsilon) and end_seconds <= (record["end"] + epsilon):
            return int(record["id"])

    midpoint = (start_seconds + end_seconds) / 2.0
    best_record_id = int(records[0]["id"])
    best_delta = None
    for record in records:
        if speaker_id is not None and int(record.get("speaker_id", speaker_id)) != int(speaker_id):
            continue
        if record["start"] <= midpoint <= record["end"]:
            return int(record["id"])
        delta = min(abs(midpoint - record["start"]), abs(midpoint - record["end"]))
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_record_id = int(record["id"])
    return best_record_id


def _build_words_payload(transcription_payload, phrase_records, segment_records):
    """Builds the top-level `words` dictionary."""
    normalized_words = _normalize_words(transcription_payload)
    if not normalized_words:
        return {}

    if not phrase_records:
        phrase_records = [
            {
                "id": 0,
                "start": normalized_words[0]["start"],
                "end": normalized_words[-1]["end"],
                "speaker_raw": normalized_words[0].get("speaker", 0),
                "text": _words_to_text(normalized_words),
            }
        ]

    speaker_map = {}
    for segment_record in segment_records:
        speaker_map[str(segment_record.get("speaker_raw"))] = int(segment_record["speaker_id"])

    group_ids = _assign_group_ids(normalized_words)
    words_payload = {}

    for word_index, word in enumerate(normalized_words):
        start_seconds = _safe_float(word.get("start"), 0.0)
        end_seconds = _safe_float(word.get("end"), start_seconds)
        if end_seconds < start_seconds:
            end_seconds = start_seconds

        speaker_id = int(speaker_map.get(str(word.get("speaker", 0)), 0))
        phrase_id = _find_record_id(phrase_records, start_seconds, end_seconds)
        segment_id = _find_record_id(segment_records, start_seconds, end_seconds, speaker_id=speaker_id)

        words_payload[word_index] = {
            "word": _clean_text(word.get("text")),
            "start": int(round(start_seconds * 1000.0)),
            "end": int(round(end_seconds * 1000.0)),
            "group_id": int(group_ids.get(word_index, 0)),
            "speaker_id": speaker_id,
            "phrase_id": int(phrase_id),
            "segment_id": int(segment_id),
        }

    return words_payload


def _build_segments_payload(segment_records):
    """Builds the top-level `segments` dictionary."""
    segments_payload = {}
    for segment_record in segment_records or []:
        start_seconds = _safe_float(segment_record.get("start"), 0.0)
        end_seconds = _safe_float(segment_record.get("end"), start_seconds)
        if end_seconds < start_seconds:
            end_seconds = start_seconds

        segments_payload[int(segment_record["id"])] = {
            "speaker_id": int(segment_record.get("speaker_id", 0)),
            "start": int(round(start_seconds * 1000.0)),
            "end": int(round(end_seconds * 1000.0)),
            "start_time": segment_record.get("start_time") or "00:00:00",
            "end_time": segment_record.get("end_time") or "00:00:00",
            "text": _clean_text(segment_record.get("text")),
        }

    return segments_payload


def _build_silences_payload(transcription_payload):
    """Builds the top-level `silences` dictionary from exact word gaps."""
    normalized_words = _normalize_words(transcription_payload)
    silences_payload = {}

    for word_index in range(len(normalized_words) - 1):
        current_word = normalized_words[word_index]
        next_word = normalized_words[word_index + 1]
        silence_start = _safe_float(current_word.get("end"), 0.0)
        silence_end = _safe_float(next_word.get("start"), silence_start)
        gap_seconds = silence_end - silence_start
        if gap_seconds < _SILENCE_MIN_GAP_SECONDS:
            continue

        start_ms = int(round(silence_start * 1000.0))
        end_ms = int(round(silence_end * 1000.0))
        silences_payload[len(silences_payload)] = {
            "start": start_ms,
            "end": end_ms,
            "duration": max(0, end_ms - start_ms),
        }

    return silences_payload


def _build_transcription_metadata(transcription_payload, segment_records):
    """Builds exact metadata for the final transcription bundle."""
    normalized_words = _normalize_words(transcription_payload)
    duration_ms = int(round(max(0.0, _get_audio_duration_seconds(transcription_payload)) * 1000.0))

    speaker_stats = {}
    total_speech_seconds = 0.0
    total_word_count = len(normalized_words)
    total_character_count = _count_characters_from_words(normalized_words)

    for segment in segment_records or []:
        speaker_id = int(segment.get("speaker_id", 0))
        start_seconds = _safe_float(segment.get("start"), 0.0)
        end_seconds = _safe_float(segment.get("end"), start_seconds)
        if end_seconds < start_seconds:
            end_seconds = start_seconds

        duration_seconds = max(0.0, end_seconds - start_seconds)
        total_speech_seconds += duration_seconds

        if speaker_id not in speaker_stats:
            speaker_stats[speaker_id] = {
                "spoken_seconds": 0.0,
                "first_speech": None,
                "last_speech": 0.0,
                "word_count": 0,
                "character_count": 0,
            }

        stats = speaker_stats[speaker_id]
        stats["spoken_seconds"] += duration_seconds
        if stats["first_speech"] is None or start_seconds < stats["first_speech"]:
            stats["first_speech"] = start_seconds
        stats["last_speech"] = max(stats["last_speech"], end_seconds)

        segment_words = segment.get("words") or []
        stats["word_count"] += len(segment_words)
        stats["character_count"] += _count_characters_from_words(segment_words)

    if not normalized_words:
        total_word_count = sum(stats["word_count"] for stats in speaker_stats.values())
        total_character_count = sum(stats["character_count"] for stats in speaker_stats.values())

    speaker_details = {}
    for speaker_id in sorted(speaker_stats):
        stats = speaker_stats[speaker_id]
        spoken_ms = int(round(max(0.0, stats["spoken_seconds"]) * 1000.0))
        spoken_minutes = spoken_ms / 60000.0
        speaker_details[speaker_id] = {
            "spoken_ms": spoken_ms,
            "speech_audio_percent": _format_percentage((spoken_ms / duration_ms) * 100.0 if duration_ms > 0 else 0.0),
            "first_speech_at": _to_hhmmss(int(math.floor(max(0.0, stats["first_speech"] or 0.0)))),
            "last_speech_at": _to_hhmmss(int(math.ceil(max(0.0, stats["last_speech"])))),
            "word_count": int(stats["word_count"]),
            "character_count": int(stats["character_count"]),
            "approximate_words_per_minute": int(round((stats["word_count"] / spoken_minutes) if spoken_minutes > 0 else 0.0)),
            "approximate_characters_per_minute": int(round((stats["character_count"] / spoken_minutes) if spoken_minutes > 0 else 0.0)),
        }

    return {
        "duration": duration_ms,
        "speaker_count": len(speaker_stats),
        "speech_coverage_percent": _format_percentage(
            ((total_speech_seconds * 1000.0) / duration_ms) * 100.0 if duration_ms > 0 else 0.0
        ),
        "word_count": int(total_word_count),
        "character_count": int(total_character_count),
        "speaker_details": speaker_details,
    }


def _build_metadata_markdown(metadata, language):
    """Builds the markdown representation for metadata."""
    overview_rows = [
        [_translate(language, "duration_ms"), int(metadata.get("duration", 0))],
        [_translate(language, "speaker_count"), int(metadata.get("speaker_count", 0))],
        [_translate(language, "speech_coverage"), f'{metadata.get("speech_coverage_percent", 0.0)}%'],
        [_translate(language, "word_count"), int(metadata.get("word_count", 0))],
        [_translate(language, "character_count"), int(metadata.get("character_count", 0))],
    ]

    markdown_parts = [
        f'# {_translate(language, "transcription_metadata")}',
        "",
        f'## {_translate(language, "overview")}',
        "",
        _build_markdown_table(
            [_translate(language, "metric"), _translate(language, "value")],
            overview_rows,
        ),
    ]

    speaker_details = metadata.get("speaker_details") or {}
    if speaker_details:
        speaker_rows = []
        for speaker_id, detail in sorted(speaker_details.items()):
            speaker_rows.append(
                [
                    speaker_id,
                    int(detail.get("spoken_ms", 0)),
                    f'{detail.get("speech_audio_percent", 0.0)}%',
                    detail.get("first_speech_at") or "00:00:00",
                    detail.get("last_speech_at") or "00:00:00",
                    int(detail.get("word_count", 0)),
                    int(detail.get("character_count", 0)),
                    int(detail.get("approximate_words_per_minute", 0)),
                    int(detail.get("approximate_characters_per_minute", 0)),
                ]
            )
        markdown_parts.extend(
            [
                "",
                f'## {_translate(language, "speaker_details")}',
                "",
                _build_markdown_table(
                    [
                        _translate(language, "speaker"),
                        _translate(language, "spoken_ms"),
                        _translate(language, "audio_share"),
                        _translate(language, "first_speech"),
                        _translate(language, "last_speech"),
                        _translate(language, "words"),
                        _translate(language, "characters"),
                        _translate(language, "words_per_min"),
                        _translate(language, "characters_per_min"),
                    ],
                    speaker_rows,
                ),
            ]
        )
    else:
        markdown_parts.extend(
            [
                "",
                f'## {_translate(language, "speaker_details")}',
                "",
                _translate(language, "no_speaker_details"),
            ]
        )

    markdown_parts.extend(
        [
            "",
            f'## {_translate(language, "notes")}',
            "",
            f'- {_translate(language, "note_segment_times")}',
            f'- {_translate(language, "note_duration")}',
        ]
    )

    return "\n".join(markdown_parts).strip()


def _build_diarized_markdown(segment_records, language):
    """Builds the markdown representation for the diarized transcription."""
    markdown_parts = [f'# {_translate(language, "diarized_transcription")}', ""]

    for segment_index, segment in enumerate(segment_records, start=1):
        markdown_parts.extend(
            [
                f'## {_translate(language, "segment_heading", segment_number=segment_index, speaker_label=_speaker_label(language, segment["speaker_id"]))}',
                "",
                f'**{_translate(language, "time_label")}:** `{segment.get("start_time", "00:00:00")}` to `{segment.get("end_time", "00:00:00")}`',
                "",
                _clean_text(segment.get("text")) or _translate(language, "no_transcription_text"),
            ]
        )
        if segment_index < len(segment_records):
            markdown_parts.extend(["", "---", ""])

    return "\n".join(markdown_parts).strip()


def _build_markdown_payload(metadata, segment_records, language_mkd):
    """Builds the top-level markdown payload."""
    language = _normalize_language_mkd(language_mkd)
    if language is False:
        return None

    return {
        "metadata": _build_metadata_markdown(metadata, language),
        "diarized": _build_diarized_markdown(segment_records, language),
    }


def _build_transcription_bundle(
    transcription_payload,
    language_mkd="en",
    request_id=None,
    cost_usd=None,
    cost_source="unavailable",
    cost_is_estimated=False,
    cost_lookup_error=None,
    cost_currency="USD",
    cost_details=None,
):
    """Builds the final flattened transcription bundle from the raw payload."""
    payload = _ensure_payload(transcription_payload)
    transcription_info = _get_transcription_info(payload)
    segment_records = _build_diarized_segment_records(payload)
    phrase_records = _build_phrase_records(payload)
    metadata = _build_transcription_metadata(payload, segment_records)
    phrases = _build_phrases_payload(phrase_records, segment_records)
    segments = _build_segments_payload(segment_records)
    words = _build_words_payload(payload, phrase_records, segment_records)
    silences = _build_silences_payload(payload)

    if isinstance(request_id, str):
        request_items = [request_id]
    else:
        request_items = list(request_id or [])

    normalized_request_ids = []
    for item in request_items:
        cleaned_item = _clean_text(item)
        if cleaned_item and cleaned_item not in normalized_request_ids:
            normalized_request_ids.append(cleaned_item)

    bundle_payload = _compact_value(
        {
            "provider": _clean_text(transcription_info.get("provider")),
            "model": _clean_text(transcription_info.get("model")),
            "language": _get_language_code(payload),
            "language_confidence": _safe_float(transcription_info.get("language_confidence"), None)
            if transcription_info.get("language_confidence") is not None
            else None,
            "text": _get_transcript_text(payload),
            "request_id": normalized_request_ids,
            "duration": metadata["duration"],
            "speaker_count": metadata["speaker_count"],
            "speech_coverage_percent": metadata["speech_coverage_percent"],
            "word_count": metadata["word_count"],
            "character_count": metadata["character_count"],
            "speaker_details": metadata["speaker_details"],
            "phrases": phrases,
            "segments": segments,
            "words": words,
            "silences": silences,
            "provider_metadata": transcription_info.get("provider_metadata"),
        }
    )
    bundle_payload["cost_usd"] = _normalize_cost_usd(cost_usd)
    bundle_payload["cost_currency"] = _clean_text(cost_currency) or "USD"
    bundle_payload["cost_source"] = _normalize_cost_source(cost_source)
    bundle_payload["cost_is_estimated"] = bool(cost_is_estimated)
    bundle_payload["cost_details"] = dict(cost_details or {})
    bundle_payload["cost_lookup_error"] = _sanitize_cost_lookup_error(cost_lookup_error)

    markdown_payload = _build_markdown_payload(metadata, segment_records, language_mkd)
    if markdown_payload is not None:
        bundle_payload["mkd"] = markdown_payload

    return bundle_payload
