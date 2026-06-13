"""Read-only catalog for public music generation options."""

from copy import deepcopy

from ._model_registry import DEFAULT_MODELS, MODEL_ALIASES, model_key_for


def get_generation_options(api=None, model=None):
    """Return local metadata for implemented generation options.

    Args:
        api: Optional. Provider key. Use a valid provider key to filter the
            detailed catalog. Use `True` with `model=True` to return the index
            summary.
        model: Optional. Standardized model key. Native provider model IDs are
            treated as invalid filters. Use `True` with `api=True` to return the
            index summary.

    Returns:
        A detailed catalog or an index summary. Invalid filters return the index
        summary instead of raising `ValueError`.
    """
    if api is True and model is True:
        return _index_summary()

    if api is None and model is None:
        return _catalog()

    valid_apis = _api_keys()
    valid_models = _model_keys()

    if api is not None and api not in valid_apis:
        return _index_summary()
    if model is not None and model not in valid_models:
        return _index_summary()

    if api is not None and model is not None and api not in _apis_for_model(model):
        return _index_summary()

    return _catalog(api=api, model=model)


def _catalog(api=None, model=None):
    catalog = {}
    for provider, models in MODEL_ALIASES.items():
        if api is not None and provider != api:
            continue
        for model_key, native_model in models.items():
            if model is not None and model_key != model:
                continue
            catalog.setdefault(model_key, {})[provider] = _parameters_for(provider, native_model)
    return deepcopy(catalog)


def _index_summary():
    return {
        "models": _model_keys(),
        "apis": _api_keys(),
        "model_apis": {model_key: _apis_for_model(model_key) for model_key in _model_keys()},
        "default_models": {
            provider: model_key_for(provider, native_model)
            for provider, native_model in DEFAULT_MODELS.items()
        },
    }


def _api_keys():
    return list(MODEL_ALIASES)


def _model_keys():
    keys = []
    for models in MODEL_ALIASES.values():
        for model_key in models:
            if model_key not in keys:
                keys.append(model_key)
    return keys


def _apis_for_model(model_key):
    return [
        provider
        for provider, models in MODEL_ALIASES.items()
        if model_key in models
    ]


def _parameters_for(provider, native_model):
    if provider == "deapi":
        return _deapi_parameters(native_model)
    if provider == "elevenlabs":
        return _elevenlabs_parameters()
    if provider == "google":
        return _google_parameters(native_model)
    if provider == "runware":
        return _runware_parameters(native_model)
    return {}


def _base_text_parameters(provider):
    prompt_field = {
        "deapi": "caption",
        "elevenlabs": "prompt",
        "google": "contents[].parts[].text",
        "runware": "positivePrompt",
    }[provider]
    lyrics_field = {
        "deapi": "lyrics",
        "elevenlabs": "prompt",
        "google": "contents[].parts[].text",
        "runware": "settings.lyrics",
    }[provider]

    return {
        "lyrics": _option(
            True,
            None,
            "Free-form song lyric text.",
            "Main sung content or lyric input used by the provider.",
            lyrics_field,
            "Use normal lyric text. Optional section tags are part of the text.",
        ),
        "style": _option(
            False,
            None,
            "Exact file stem from easy_ai_clients/music/styles/*.py, without the .py extension.",
            "Builds a local prompt and safe kwargs from a preset. If prompt is also passed, the explicit prompt replaces the preset prompt.",
            "easy_ai_clients.music._style_adapter",
            "Use a reusable local style preset.",
        ),
        "language": _option(
            False,
            None,
            "Accepts pt-BR, pt-PT, en-US, en-GB, en-IE, es-ES, fr-FR, or de-DE.",
            "Local language override for style-generated prompts. ACE-Step models also receive mapped vocal_language.",
            "easy_ai_clients.music._style_adapter",
            "Use with style to override the preset vocal language.",
        ),
        "prompt": _option(
            False,
            None,
            "Free-form text. Required when style is not used.",
            "Describes genre, arrangement, voice, mix, and musical intent. With style, it replaces the preset prompt.",
            prompt_field,
            "Use for direct musical direction.",
        ),
    }


def _deapi_parameters(native_model):
    parameters = _base_text_parameters("deapi")
    parameters.update(
        {
            "duration": _option(
                False,
                60,
                "Integer or number in seconds. Accepts 10 to 600.",
                "Sets the duration sent in the payload. When omitted, the wrapper sends 60.",
                "duration",
                "Use to request a shorter or longer song within the local limit.",
            ),
            "steps": _option(
                False,
                8,
                _deapi_steps_values(native_model),
                "Controls inference_steps. When omitted, the wrapper sends 8.",
                "inference_steps",
                "Use to adjust the inference effort allowed by the model.",
            ),
            "bpm": _option(
                False,
                116,
                "Number from 30 to 300 when provided. None is not blocked by local validation.",
                "Sets the tempo sent to the provider.",
                "bpm",
                "Use to control rhythmic tempo.",
            ),
            "key_scale": _option(
                False,
                "A minor",
                "Free-form text. There is no local enum.",
                "Sets the key and scale sent to the provider.",
                "keyscale",
                "Use to guide harmony.",
            ),
            "time_signature": _option(
                False,
                4,
                "Accepts 2, 3, 4, or 6.",
                "Sets the time signature sent to the provider.",
                "timesignature",
                "Use to guide rhythmic division.",
            ),
            "vocal_language": _option(
                False,
                "pt",
                "Free-form text. There is no local enum.",
                "Sets the vocal language sent to the provider.",
                "vocal_language",
                "Use to guide pronunciation and sung language.",
            ),
            "reference_audio": _option(
                False,
                None,
                "Local audio file path.",
                "When provided, the wrapper opens the local file and sends multipart data.",
                "reference_audio",
                "Use to provide a local audio reference to the provider.",
            ),
            "webhook_url": _option(
                False,
                None,
                "Free-form URL. There is no local HTTPS validation.",
                "Passed through to the payload for job status notifications.",
                "webhook_url",
                "Use when the provider should call an external URL.",
            ),
        }
    )
    return parameters


def _elevenlabs_parameters():
    parameters = _base_text_parameters("elevenlabs")
    parameters["duration"] = _option(
        False,
        60,
        "Number in seconds. Accepts 3 to 600.",
        "The wrapper converts this to music_length_ms. When omitted, it uses 60 seconds.",
        "music_length_ms",
        "Use to control composition duration.",
    )
    return parameters


def _google_parameters(native_model):
    parameters = _base_text_parameters("google")
    practical_use = "Accepted to keep the standardized contract, but it does not change the provider payload."
    if native_model == "lyria-3-clip-preview":
        practical_use = (
            "Accepted for standardization and ignored in the payload. "
            "When style builds the prompt, the text targets about 30 seconds."
        )
    parameters["duration"] = _option(
        False,
        None,
        "Accepted by the local wrapper, but ignored in the provider payload.",
        "Not sent to the provider.",
        "Not sent",
        practical_use,
    )
    return parameters


def _runware_parameters(native_model):
    parameters = _base_text_parameters("runware")
    parameters.update(
        {
            "duration": _option(
                False,
                None,
                "Number in seconds. Accepts 30 to 300 when provided.",
                "Optional. When omitted, it is not sent in the payload.",
                "duration",
                "Use only when you want to send this duration control to the provider.",
            ),
            "steps": _option(
                False,
                None,
                _runware_steps_values(native_model),
                "Optional. When omitted, it is not sent in the payload.",
                "steps",
                "Use to adjust the inference effort allowed by the model.",
            ),
            "bpm": _option(
                False,
                None,
                "Number from 30 to 300 when provided.",
                "Optional. When omitted, it is not sent in the payload.",
                "settings.bpm",
                "Use to control rhythmic tempo.",
            ),
            "key_scale": _option(
                False,
                None,
                "Free-form text. There is no local enum.",
                "Optional. When omitted, it is not sent in the payload.",
                "settings.keyScale",
                "Use to guide harmony.",
            ),
            "time_signature": _option(
                False,
                None,
                "Accepts 2, 3, 4, or 6.",
                "Optional. When omitted, it is not sent in the payload.",
                "settings.timeSignature",
                "Use to guide rhythmic division.",
            ),
            "vocal_language": _option(
                False,
                None,
                "Accepts unknown or an ISO 639-1 code present in the wrapper's local list.",
                "Optional. When omitted, it is not sent in the payload.",
                "settings.vocalLanguage",
                "Use to guide pronunciation and sung language.",
            ),
        }
    )
    if native_model == "runware:ace-step@v1.5-xl-sft":
        parameters["negative_prompt"] = _option(
            False,
            None,
            "Free-form text. Accepted only by the Runware XL SFT model.",
            "Sent as negativePrompt when not None. With style, it can come from the preset negative_traits.",
            "negativePrompt",
            "Use to list characteristics the model should avoid.",
        )
    return parameters


def _deapi_steps_values(native_model):
    return "Accepts 1 to 8."


def _runware_steps_values(native_model):
    if native_model in {
        "runware:ace-step@v1.5-xl-base",
        "runware:ace-step@v1.5-xl-sft",
    }:
        return "Accepts 1 to 300."
    return "Accepts 1 to 20."


def _option(required, default, accepted_values, description, provider_field, practical_use):
    return {
        "required": required,
        "default": default,
        "accepted_values": accepted_values,
        "description": description,
        "practical_use": practical_use,
        "provider_field": provider_field,
    }


