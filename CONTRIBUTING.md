# Contributing to easy-ai-clients

Thank you for considering a contribution! This document describes the local
development workflow and the release process.

## Development setup

```bash
git clone https://github.com/reiarthur/easy-ai-clients.git
cd easy-ai-clients
python -m venv .venv
.venv/Scripts/activate  # PowerShell: .venv\Scripts\Activate.ps1; Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

Set the environment variables of the providers you intend to exercise (only
those you actually need). See [`.env.example`](.env.example) for the
recognised names. Use [`python-dotenv`](https://pypi.org/project/python-dotenv/)
or your own loader when local development depends on a `.env` file. Some
adapters also read `.env` from the current working directory, but tests and
scripts should load secrets explicitly when they require them.

## Running tests

The bundled test suite focuses on package-level invariants (imports,
dispatcher routing, parameter validation). It does not call paid APIs.

```bash
pytest
```

To run a specific file:

```bash
pytest tests/test_imports.py -v
```

Paid integration smoke tests are gated by explicit environment variables and
provider credentials. For video, set `EASY_AI_CLIENTS_LIVE_VIDEO=1` plus the
credentials for the providers you want to exercise. The current video smoke
budget is guarded at US$ 1.00.

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
├── __init__.py            # Top-level package: re-exports text, audio, image, video, __version__
├── py.typed
├── text/
│   ├── __init__.py        # Text generate dispatcher
│   ├── pre_processing.py  # Shared HTTP and env helpers
│   ├── post_processing.py # Output extraction and cost helpers
│   └── _apis/             # PRIVATE provider modules (one file per provider)
├── audio/
│   ├── __init__.py        # Audio generate / transcribe dispatchers
│   ├── _synthesize/...    # PRIVATE TTS providers
│   └── _transcribe/...    # PRIVATE STT providers
├── image/
    ├── __init__.py        # Image generate / edit / remix / analyze dispatchers
    ├── _common/           # PRIVATE shared image helpers (HTTP, cost, mask, etc.)
    ├── _generate/...      # PRIVATE image generation providers
    ├── _edit/...
    ├── _remix/...
    └── _analyze/...
└── video/
    ├── __init__.py        # Video generation dispatchers and async helpers
    ├── _shared/           # PRIVATE shared video helpers
    ├── _text_to_video/...
    ├── _image_to_video/...
    ├── _motion_control/...
    ├── _image_lipsync/...
    └── _video_lipsync/...
```

Anything starting with `_` is internal. The only stable surface is what is
explicitly exported from `easy_ai_clients.text`, `easy_ai_clients.audio`,
`easy_ai_clients.image`, and `easy_ai_clients.video`.

## Adding a new provider

1. Pick a short, lowercase identifier matching the file name (e.g. `groq`).
2. Drop the new module under the appropriate `_apis/` directory and expose a
   public function with the operation's standard signature
   (`generate`, `edit`, `remix`, `analyze`, `transcribe`, or a video operation).
3. Register the new identifier in the dispatcher's tuple inside the operation
   `__init__.py` (e.g. `_AVAILABLE_APIS` for `text`, `_GENERATE_APIS` for
   `image.generate`).
4. Add the credential variable to `.env.example` and document the provider in
   [`docs/providers.md`](docs/providers.md).
5. Update `CHANGELOG.md` under a new `[Unreleased]` section.

## Building the package

```bash
python -m build
twine check dist/*
```

Both must pass before publishing.

## Publishing to PyPI

```bash
python -m build
TWINE_USERNAME=__token__ TWINE_PASSWORD=<project-token> twine upload dist/*
```

The token must be scoped to the `easy-ai-clients` project. After uploading,
verify the new release at `https://pypi.org/project/easy-ai-clients/<version>/`.
Do not store PyPI credentials in `.pypirc`, shell profiles, docs, or committed
files for one-off releases.

### Bumping the version

Update the version in two places and add a `CHANGELOG.md` entry:

1. `pyproject.toml` — `version = "X.Y.Z"`
2. `src/easy_ai_clients/__init__.py` — `__version__ = "X.Y.Z"`
