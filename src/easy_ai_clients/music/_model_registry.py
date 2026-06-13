"""Provider-scoped model aliases used by the public runtime."""

PROVIDERS = (
    "deapi",
    "elevenlabs",
    "google",
    "runware",
)

MODEL_ALIASES = {
    "deapi": {
        "ace_step_v1_5_turbo": "AceStep_1_5_Turbo",
        "ace_step_1_5_xl_turbo_int8": "AceStep_1_5_XL_Turbo_INT8",
    },
    "elevenlabs": {
        "eleven_music": "music_v1",
    },
    "google": {
        "lyria_3_clip_preview": "lyria-3-clip-preview",
        "lyria_3_pro_preview": "lyria-3-pro-preview",
    },
    "runware": {
        "ace_step_v1_5_turbo": "runware:ace-step@v1.5-turbo",
        "ace_step_v1_5_xl_base": "runware:ace-step@v1.5-xl-base",
        "ace_step_v1_5_xl_sft": "runware:ace-step@v1.5-xl-sft",
        "ace_step_v1_5_xl_turbo": "runware:ace-step@v1.5-xl-turbo",
    },
}

DEFAULT_MODELS = {
    "deapi": "AceStep_1_5_Turbo",
    "elevenlabs": "music_v1",
    "google": "lyria-3-clip-preview",
    "runware": "runware:ace-step@v1.5-xl-turbo",
}


def resolve_model(provider, model):
    """Return the provider-native model ID and standardized model key.

    Args:
        provider: Required. Provider key.
        model: Optional. Provider-native model ID or standardized model key.
            When omitted, the provider-specific validated default is used.

    Returns:
        A tuple with `(native_model, model_key)`.

    Raises:
        ValueError: If the model is empty or unsupported for the provider.
    """
    if model is None or not str(model).strip():
        model = DEFAULT_MODELS.get(provider)
    if not model:
        raise ValueError("model is required")

    value = str(model).strip()
    aliases = MODEL_ALIASES.get(provider, {})
    if value in aliases:
        return aliases[value], value

    reverse = {native: key for key, native in aliases.items()}
    if value in reverse:
        return value, reverse[value]

    raise ValueError(f"Unsupported model for {provider}: {model}")


def model_key_for(provider, model):
    """Return the standardized key for a provider-native model ID."""
    return resolve_model(provider, model)[1]


