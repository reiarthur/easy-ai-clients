"""Resolve reusable music styles into provider-safe generation requests."""

import importlib
from copy import deepcopy
from pathlib import Path

STYLE_DIR = Path(__file__).resolve().parent / "styles"

_LANGUAGE_LABELS = {
    "pt-BR": "Brazilian Portuguese",
    "en-US": "English",
    "en-GB": "British English",
    "en-IE": "Irish English",
    "es-ES": "Spanish",
    "pt-PT": "European Portuguese",
    "fr-FR": "French",
    "de-DE": "German",
}

_ACE_STEP_LANGUAGE_CODES = {
    "pt-BR": "pt",
    "pt-PT": "pt",
    "en-US": "en",
    "en-GB": "en",
    "en-IE": "en",
    "es-ES": "es",
    "fr-FR": "fr",
    "de-DE": "de",
}

_DEAPI_ACE_STEP_MODELS = {
    "AceStep_1_5_Turbo",
    "AceStep_1_5_XL_Turbo_INT8",
}

_GOOGLE_LYRIA_MODELS = {
    "lyria-3-clip-preview",
    "lyria-3-pro-preview",
}

_RUNWARE_ACE_STEPS = {
    "runware:ace-step@v1.5-turbo": 10,
    "runware:ace-step@v1.5-xl-base": 100,
    "runware:ace-step@v1.5-xl-turbo": 8,
    "runware:ace-step@v1.5-xl-sft": 80,
}

_RUNWARE_NEGATIVE_MODELS = {
    "runware:ace-step@v1.5-xl-sft",
}


def list_styles():
    """Return exact predefined style names from `music/styles/`."""
    return sorted(
        path.stem
        for path in STYLE_DIR.glob("*.py")
        if path.name != "__init__.py"
    )


def get_style_presets(fields=None, styles=None):
    """Return copied style presets with optional exact filters.

    Args:
        fields: Optional. Use `None` for full presets, a string field name, or
            a list of string field names. Field names must match preset keys.
        styles: Optional. Use `None` for all styles, a string style id, or a
            list of string style ids. Style ids must match preset `id` values.

    Returns:
        A dictionary keyed by preset `id`. Invalid filters return an error
        dictionary instead of raising an exception.
    """
    accepted_styles = list_styles()
    accepted_fields = _style_preset_fields(accepted_styles)
    selected_fields, invalid_fields = _normalize_preset_filter(fields, accepted_fields)
    selected_styles, invalid_styles = _normalize_preset_filter(styles, accepted_styles)

    if invalid_fields or invalid_styles:
        return _style_preset_filter_error(
            accepted_fields,
            accepted_styles,
            invalid_fields,
            invalid_styles,
        )

    style_ids = accepted_styles if selected_styles is None else selected_styles
    result = {}
    for style in style_ids:
        preset = _load_style_preset(style)
        preset_id = preset["id"]
        if selected_fields is None:
            result[preset_id] = deepcopy(preset)
        else:
            result[preset_id] = {
                field: deepcopy(preset[field])
                for field in selected_fields
            }
    return result


def resolve_style(style):
    """Resolve an optional exact style name to a preset request.

    Args:
        style: Optional. Exact style file stem. Use `None` for no preset.

    Returns:
        A dictionary with `style_source`, `style`, and optional `style_preset`.

    Raises:
        ValueError: If `style` is not `None` and does not match a style file.
    """
    if style is None:
        return {
            "style_source": "none",
            "style": None,
            "style_preset": None,
        }
    if _is_predefined_style(style):
        return {
            "style_source": "preset",
            "style": style,
            "style_preset": _load_style_preset(style),
        }
    raise ValueError(f"Unknown style: {style}")


def build_generation_request(
    provider,
    model,
    lyrics,
    style=None,
    prompt=None,
    kwargs=None,
):
    """Build a normalized local request without calling provider APIs.

    Args:
        provider: Required. Provider file name from `music/_apis/`.
        model: Required. Exact provider model.
        lyrics: Required. Caller-provided lyrics.
        style: Optional. Exact predefined style name. Use `None` for no preset.
        prompt: Optional. Caller prompt. If provided with a preset, it replaces
            the preset-rendered prompt.
        kwargs: Optional. Caller kwargs. These override generated preset kwargs.
            `language` is an adapter-only style override. `negative_prompt` is
            accepted inside this dictionary.

    Returns:
        A local request dictionary for `music.generate()`.
    """
    user_kwargs = dict(kwargs or {})
    language_override = user_kwargs.pop("language", None)
    user_negative_prompt_provided = "negative_prompt" in user_kwargs
    user_negative_prompt = user_kwargs.pop("negative_prompt", None)
    user_prompt = _clean_prompt_text("prompt", prompt)
    user_prompt_provided = user_prompt is not None
    if user_negative_prompt_provided:
        user_negative_prompt = _clean_prompt_text("negative_prompt", user_negative_prompt)

    resolved = resolve_style(style)
    style_preset = resolved["style_preset"]
    language = _style_language(style_preset, language_override)

    if style_preset is None:
        prompt = user_prompt
        generated_kwargs = {}
        style_source = "none"
    else:
        prompt = user_prompt if user_prompt_provided else _provider_prompt(provider, model, style_preset, language)
        generated_kwargs = _provider_kwargs(provider, model, style_preset, language)
        style_source = "preset"

    if prompt is not None:
        generated_kwargs["prompt"] = prompt

    if _supports_negative_prompt(provider, model):
        negative_prompt = None
        if user_negative_prompt_provided:
            negative_prompt = user_negative_prompt
        elif style_preset is not None:
            negative_prompt = _render_negative_prompt(style_preset)
        if negative_prompt is not None:
            generated_kwargs["negative_prompt"] = negative_prompt
    elif user_negative_prompt_provided:
        generated_kwargs["negative_prompt"] = user_negative_prompt

    return {
        "lyrics": lyrics,
        "model": model,
        "kwargs": _merge_kwargs(generated_kwargs, user_kwargs),
        "style_source": style_source,
        "style": style,
    }


def _clean_prompt_text(parameter, value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{parameter} must be a string")
    text = value.strip()
    return text or None


def _load_style_preset(style):
    module = importlib.import_module(f".styles.{style}", __package__)
    return module.STYLE_PRESET


def _style_preset_fields(styles):
    if not styles:
        return []
    return list(_load_style_preset(styles[0]).keys())


def _normalize_preset_filter(value, accepted_values):
    accepted = set(accepted_values)
    if value is None:
        return None, []
    if isinstance(value, str):
        if not value:
            return [], ["<empty string>"]
        if value not in accepted:
            return [], [value]
        return [value], []
    if isinstance(value, list):
        if not value:
            return [], ["<empty list>"]
        selected = []
        invalid = []
        for item in value:
            if not isinstance(item, str):
                invalid.append(f"<non-string item: {type(item).__name__}>")
            elif not item:
                invalid.append("<empty string>")
            elif item not in accepted:
                invalid.append(item)
            else:
                selected.append(item)
        return selected, invalid
    return [], [f"<invalid type: {type(value).__name__}>"]


def _style_preset_filter_error(
    accepted_fields,
    accepted_styles,
    invalid_fields,
    invalid_styles,
):
    return {
        "error": {
            "message": "Invalid style preset filters.",
            "usage": {
                "fields": "Use None, a string field name, or a list of string field names.",
                "styles": "Use None, a string style id, or a list of string style ids.",
            },
            "accepted_fields": accepted_fields,
            "accepted_styles": accepted_styles,
            "invalid_fields": invalid_fields,
            "invalid_styles": invalid_styles,
        }
    }


def _is_predefined_style(style):
    return style in list_styles()


def _style_language(style_preset, language_override):
    if language_override is not None:
        return _validate_language(language_override)
    if style_preset is None:
        return None
    return _validate_language(style_preset["default_language"])


def _validate_language(language):
    if not isinstance(language, str):
        raise ValueError("language must be a string")
    text = language.strip()
    if text not in _LANGUAGE_LABELS:
        accepted = ", ".join(sorted(_LANGUAGE_LABELS))
        raise ValueError(f"language must be one of: {accepted}")
    return text


def _provider_prompt(provider, model, style_preset, language):
    if provider == "deapi" and model in _DEAPI_ACE_STEP_MODELS:
        return _render_prompt(
            style_preset,
            language,
            compact=True,
            max_chars=300,
        )
    if provider == "google" and model == "lyria-3-clip-preview":
        return _render_prompt(
            style_preset,
            language,
            duration_seconds=30,
        )
    return _render_prompt(style_preset, language)


def _render_prompt(
    style_preset,
    language,
    compact=False,
    duration_seconds=None,
    max_chars=None,
):
    language = _language_label(language)
    vocal = style_preset["default_vocal"]["description"]
    duration = duration_seconds or style_preset["duration_seconds"]
    bpm = style_preset["tempo_bpm"]
    key_scale = style_preset["key_scale"]

    if compact:
        return _render_compact_prompt(
            style_preset,
            language,
            vocal,
            duration,
            bpm,
            key_scale,
            max_chars,
        )

    instruments = ", ".join(style_preset["instrumentation"][:5])
    arrangement = ", ".join(style_preset["arrangement"])
    mood = ", ".join(style_preset["mood"])
    parts = [
        style_preset["style_prompt"],
        vocal,
        f"{language} lyrics",
        f"{bpm} BPM",
        key_scale,
        f"{style_preset['time_signature']}/4 time",
        f"target duration around {duration} seconds",
        f"{style_preset['energy']} energy",
        f"{mood} mood",
        instruments,
        arrangement,
        style_preset["mix_target"],
    ]

    text = _sentence(parts)
    if max_chars is None or len(text) <= max_chars:
        return text
    return _render_compact_prompt(
        style_preset,
        language,
        vocal,
        duration,
        bpm,
        key_scale,
        max_chars,
    )


def _render_compact_prompt(
    style_preset,
    language,
    vocal,
    duration,
    bpm,
    key_scale,
    max_chars,
):
    instruments = ", ".join(style_preset["instrumentation"][:4])
    critical = [
        style_preset["style_family"],
        vocal,
        f"{language} lyrics",
        f"{bpm} BPM",
        key_scale,
        instruments,
        style_preset["mix_target"],
    ]
    optional = [
        f"{style_preset['time_signature']}/4 time",
        f"around {duration} seconds",
    ]

    text = _sentence(critical + optional)
    if max_chars is None or len(text) <= max_chars:
        return text

    shorter_critical = [
        style_preset["style_family"],
        vocal,
        f"{language} lyrics",
        f"{bpm} BPM",
        key_scale,
        ", ".join(style_preset["instrumentation"][:2]),
        _clip(style_preset["mix_target"], 72),
    ]
    text = _sentence(shorter_critical)
    if len(text) <= max_chars:
        return text

    shortest_critical = [
        _clip(style_preset["style_family"], 42),
        _clip(vocal, 58),
        f"{language} lyrics",
        f"{bpm} BPM",
        key_scale,
        _clip(style_preset["instrumentation"][0], 42),
        _clip(style_preset["mix_target"], 54),
    ]
    return _clip(_sentence(shortest_critical), max_chars)


def _render_negative_prompt(style_preset):
    traits = style_preset.get("negative_traits") or []
    return ", ".join(traits) or None


def _provider_kwargs(provider, model, style_preset, language):
    if provider == "deapi" and model in _DEAPI_ACE_STEP_MODELS:
        return {
            "duration": style_preset["duration_seconds"],
            "steps": 8,
            "bpm": style_preset["tempo_bpm"],
            "key_scale": style_preset["key_scale"],
            "time_signature": style_preset["time_signature"],
            "vocal_language": _ace_step_language(language),
        }

    controls = style_preset["generation_controls"]

    if provider == "elevenlabs" and model == "music_v1":
        return {
            "duration": style_preset["duration_seconds"],
            "_force_instrumental": controls["instrumental"],
        }

    if provider == "google" and model in _GOOGLE_LYRIA_MODELS:
        return {"duration": style_preset["duration_seconds"]}

    if provider == "runware" and model in _RUNWARE_ACE_STEPS:
        kwargs = {
            "duration": style_preset["duration_seconds"],
            "steps": _RUNWARE_ACE_STEPS[model],
            "bpm": style_preset["tempo_bpm"],
            "key_scale": style_preset["key_scale"],
            "time_signature": style_preset["time_signature"],
            "vocal_language": _ace_step_language(language),
        }
        return kwargs

    return {}


def _merge_kwargs(generated_kwargs, user_kwargs):
    merged = dict(generated_kwargs)
    merged.update(user_kwargs)
    return merged


def _supports_negative_prompt(provider, model):
    return provider == "runware" and model in _RUNWARE_NEGATIVE_MODELS


def _language_label(language):
    return _LANGUAGE_LABELS.get(language, language)


def _ace_step_language(language):
    return _ACE_STEP_LANGUAGE_CODES.get(language, "unknown")


def _sentence(parts):
    text = ", ".join(str(part).strip() for part in parts if str(part).strip())
    if text.endswith("."):
        return text
    return f"{text}."


def _clip(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip(" ,.;:") + "..."


