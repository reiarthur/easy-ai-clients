import os

PROVIDER_ENV_VARS = {
    "google": ("GOOGLE_API_KEY",),
    "elevenlabs": ("ELEVENLABS_API_KEY",),
    "stability": ("STABILITY_API_KEY",),
    "beatoven": ("BEATOVEN_API_KEY",),
    "musicfy": ("MUSICFY_API_KEY",),
    "minimax": ("MINIMAX_API_KEY",),
    "sonauto": ("SONAUTO_API_KEY",),
    "jen": ("JEN_MUSIC_API_KEY",),
    "musicgpt": ("MUSICGPT_API_KEY",),
    "topmediai": ("TOPMEDIAI_API_KEY",),
    "modelslab": ("MODELSLAB_API_KEY",),
    "segmind": ("SEGMIND_API_KEY",),
    "falai": ("FAL_KEY",),
    "replicate": ("REPLICATE_API_TOKEN",),
    "generatesongs": ("GENERATESONGS_API_KEY",),
    "wavespeedai": ("WAVESPEEDAI_API_KEY",),
    "soundverse": ("SOUNDVERSE_API_KEY",),
    "scenario": ("SCENARIO_API_KEY", "SCENARIO_API_SECRET"),
    "musicful": ("MUSICFUL_API_KEY",),
    "deapi": ("DEAPI_API_KEY",),
    "runware": ("RUNWARE_API_KEY",),
    "novita": ("NOVITA_API_KEY",),
    "cloudflare": ("CLOUDFLARE_API_TOKEN",),
}


def env_var_names(provider):
    """Return required environment variable names for a provider.

    Args:
        provider: Required. Lowercase provider identifier.

    Returns:
        A tuple of environment variable names.
    """
    return PROVIDER_ENV_VARS.get(provider, ())


def require_env_vars(provider):
    """Read required provider credentials from the environment.

    Args:
        provider: Required. Lowercase provider identifier.

    Returns:
        A dictionary keyed by environment variable name.

    Raises:
        RuntimeError: If the provider is unknown or any credential is missing.
    """
    names = env_var_names(provider)
    if not names:
        raise RuntimeError(f"No credential variables are configured for provider '{provider}'.")

    values = {}
    missing = []
    for name in names:
        value = os.environ.get(name)
        if value:
            values[name] = value
        else:
            missing.append(name)

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variable(s): {joined}.")

    return values


def require_env_var(name):
    """Read one required environment variable.

    Args:
        name: Required. Environment variable name.

    Returns:
        The environment variable value.

    Raises:
        RuntimeError: If the variable is missing.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}.")
    return value
