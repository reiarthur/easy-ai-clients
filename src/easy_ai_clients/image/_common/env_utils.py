"""Environment loading helpers with tolerant `.env` parsing."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path.cwd()
ENV_PATH = PROJECT_ROOT / ".env"
_ENV_WAS_LOADED = False


def load_project_env(env_path: Path | None = None) -> None:
    """Load the repository `.env` file using tolerant parsing rules.

    This helper is the canonical way to hydrate provider credentials for the
    integration layer. The project intentionally does not rely on shell
    semantics such as `source .env`, because the checked-in `.env` may contain
    spacing around `=` that is valid for a text file but inconvenient for a bash
    parser. The loader therefore:

    1. Reads the target file line by line.
    2. Ignores blank lines and comments.
    3. Trims surrounding whitespace from keys and values.
    4. Preserves any environment variable that is already present in the process.

    The function is idempotent within the current Python process and is safe to
    call repeatedly from tests, smoke runners, or provider wrappers.

    Args:
        env_path: Optional explicit `.env` path. When omitted, the project root
            `.env` is used.

    Returns:
        `None`. Environment variables are injected into `os.environ` as a side
        effect.

    Notes:
        No secrets are logged, returned, or persisted by this helper.
    """

    global _ENV_WAS_LOADED
    if _ENV_WAS_LOADED:
        return

    target = env_path or ENV_PATH
    if not target.exists():
        _ENV_WAS_LOADED = True
        return

    for raw_line in target.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        normalized_key = key.strip()
        if not normalized_key or normalized_key in os.environ:
            continue
        os.environ[normalized_key] = value.strip().strip('"').strip("'")

    _ENV_WAS_LOADED = True


def get_env(
    primary_name: str,
    *,
    aliases: Iterable[str] = (),
    required: bool = False,
) -> str | None:
    """Resolve an environment variable with optional compatibility aliases.

    Args:
        primary_name: Preferred environment-variable name used by this project
            and by provider wrappers in their public contracts.
        aliases: Optional fallback names accepted for compatibility when a
            provider is commonly configured under multiple secret names.
        required: When `True`, raise `RuntimeError` instead of returning `None`
            if no configured value is found.

    Returns:
        The resolved secret value, or `None` when the variable is optional and
        no matching name is configured.

    Raises:
        RuntimeError: If `required=True` and none of the candidate names are
            present.

    Notes:
        The lookup order is deterministic: `primary_name` first, then aliases in
        the order provided.
    """

    load_project_env()
    candidates = [primary_name, *aliases]
    for name in candidates:
        value = os.getenv(name)
        if value:
            return value
    if required:
        raise RuntimeError(
            f"Missing required environment variable. Tried: {', '.join(candidates)}"
        )
    return None


def get_provider_api_key(
    provider_label: str,
    primary_name: str,
    *,
    aliases: Iterable[str] = (),
) -> str:
    """Resolve a provider API key and raise a provider-specific error if missing.

    This helper is used by public provider entrypoints right before network
    calls. It keeps user-facing failures consistent by converting a generic
    missing-variable condition into a descriptive provider-specific error message
    such as "OpenAI API key is not available in the environment."

    Args:
        provider_label: Human-readable provider name used in error messages.
        primary_name: Preferred environment variable for the provider secret.
        aliases: Optional fallback names accepted for compatibility.

    Returns:
        The resolved API key as a non-empty string.

    Raises:
        RuntimeError: If no matching secret is available.
    """

    try:
        return get_env(primary_name, aliases=aliases, required=True) or ""
    except RuntimeError as exc:
        raise RuntimeError(
            f"{provider_label} API key is not available in the environment."
        ) from exc


def project_root() -> Path:
    """Return the absolute repository root used by this integration layer.

    Returns:
        Absolute `Path` pointing at the project root. Tests and runners use this
        helper so path resolution remains stable even when commands are launched
        from other working directories.
    """

    return PROJECT_ROOT
