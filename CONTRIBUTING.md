# Contributing to easy-ai-clients

## Development setup

Clone the repository and install the package in editable mode with all development dependencies:

```bash
git clone https://github.com/reiarthur/easy-ai-clients.git
cd easy-ai-clients
pip install -e ".[dev]"
```

The `[dev]` extra installs:

| Tool | Purpose |
|---|---|
| `build` | Build the source distribution and wheel |
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `ruff` | Linting and import sorting |
| `twine` | Upload to PyPI |

## Running tests

```bash
pytest
```

All async tests run automatically. The test suite uses fake adapters — no real API credentials are needed.

To run a single test file:

```bash
pytest tests/test_text_api.py -v
```

## Linting

```bash
ruff check src tests
```

To auto-fix safe issues:

```bash
ruff check --fix src tests
```

## Project structure

```
src/easy_ai_clients/
├── __init__.py          # Public exports (exceptions, models, EasyAiClient client)
├── client.py            # Stateful EasyAiClient client
├── exceptions.py        # Public re-exports of typed exceptions
├── models.py            # Pydantic v2 request and result models
├── text/                # Text generation helpers and provider adapters
├── audio/               # Transcription, synthesis, and music helpers and adapters
├── image/               # Image generation, transform, compose and edit helpers and adapters
├── video/               # Video generation and lip-sync helpers and adapters
└── _core/               # Internal utilities (HTTP, retry, polling, credentials, schemas)
    └── schemas/         # Internal Pydantic schemas used by the provider layer
```

The `_core` package is internal. Only import from the public modules (`easy_ai_clients`, `easy_ai_clients.text`, `easy_ai_clients.audio`, `easy_ai_clients.image`, `easy_ai_clients.video`, `easy_ai_clients.exceptions`, `easy_ai_clients.models`).

## Adding a new provider

1. Add a `ProviderSpec` entry in `src/easy_ai_clients/_core/provider_catalog.py` with the modality, operation, provider name, and required env vars.
2. Implement the adapter class in the relevant `providers/` directory (e.g., `src/easy_ai_clients/text/providers/`).
3. Register the adapter in the registry builder (`build_text_registry`, `build_audio_registries`, etc.).
4. Add the provider to the alias table in `src/easy_ai_clients/_core/aliases.py` if it has common aliases.
5. Add the provider env var to `.env.example`.
6. Update `docs/providers.md` and `README.md` with the new entry.
7. Add a test in `tests/` verifying the adapter is reachable through the public API.
8. Document the change in `CHANGELOG.md` under an `[Unreleased]` section.

## Building the package

```bash
python -m build
```

This generates two files in `dist/`:
- `easy_ai_clients-X.Y.Z.tar.gz` — source distribution
- `easy_ai_clients-X.Y.Z-py3-none-any.whl` — universal wheel

Validate the package metadata before uploading:

```bash
twine check dist/*
```

Both checks must pass (`PASSED`) before proceeding.

## Publishing to PyPI

### TestPyPI (recommended first step)

Test the upload flow without publishing to the production index:

```bash
twine upload --repository testpypi dist/*
```

You will be prompted for your TestPyPI credentials. After uploading, install from TestPyPI to verify the package works:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ easy-ai-clients
```

### PyPI (production)

```bash
twine upload dist/*
```

You will be prompted for your PyPI username and password (or API token). Use an API token instead of a password:

1. Go to [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
2. Create a token scoped to the `easy-ai-clients` project.
3. Use `__token__` as the username and the token string as the password, or store them in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-...
```

### Bumping the version

The version is defined in two places — update both together:

1. `pyproject.toml` — `version = "X.Y.Z"`
2. `src/easy_ai_clients/_core/config.py` — `VERSION = "X.Y.Z"`

After bumping, add a new section to `CHANGELOG.md` documenting the changes.
