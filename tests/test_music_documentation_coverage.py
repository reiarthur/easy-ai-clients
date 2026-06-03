from pathlib import Path

from easy_ai_clients import music
from easy_ai_clients.music._common import env_utils

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs" / "music"


def _operation_matrix():
    return {
        operation: tuple(config["apis"])
        for operation, config in music._OPERATIONS.items()
    }


def _music_doc_pages():
    if not DOCS_ROOT.exists():
        return []
    return sorted(DOCS_ROOT.glob("*/*.md"))


def test_every_operation_provider_pair_has_matching_music_doc():
    missing = []
    for operation, providers in _operation_matrix().items():
        for provider in providers:
            path = DOCS_ROOT / operation / f"{provider}.md"
            if not path.is_file():
                missing.append(path.relative_to(ROOT).as_posix())

    assert missing == []


def test_no_music_doc_exists_for_unsupported_provider_pair():
    matrix = _operation_matrix()
    unsupported = []

    for page in _music_doc_pages():
        operation = page.parent.name
        provider = page.stem
        if operation not in matrix or provider not in matrix[operation]:
            unsupported.append(page.relative_to(ROOT).as_posix())

    assert unsupported == []


def test_docs_providers_links_every_music_doc_when_present():
    providers_page = ROOT / "docs" / "providers.md"
    assert providers_page.exists()

    content = providers_page.read_text(encoding="utf-8").replace("\\", "/")
    missing_links = []

    for page in _music_doc_pages():
        relative = page.relative_to(ROOT).as_posix()
        without_docs_prefix = relative.removeprefix("docs/")
        if relative not in content and without_docs_prefix not in content:
            missing_links.append(relative)

    assert missing_links == []


def test_public_music_docs_exist_and_reference_music_module():
    expected_docs = (
        ROOT / "README.md",
        ROOT / "docs" / "providers.md",
        ROOT / "docs" / "usage.md",
        ROOT / "docs" / "operation_examples.md",
        ROOT / "docs" / "configuration.md",
    )

    missing = [
        path.relative_to(ROOT).as_posix()
        for path in expected_docs
        if not path.is_file()
    ]
    assert missing == []

    for path in expected_docs:
        content = path.read_text(encoding="utf-8")
        assert "easy_ai_clients.music" in content or "from easy_ai_clients import music" in content


def test_music_provider_docs_include_expected_credential_variables():
    missing = []

    for operation, providers in _operation_matrix().items():
        for provider in providers:
            path = DOCS_ROOT / operation / f"{provider}.md"
            content = path.read_text(encoding="utf-8")
            for env_name in env_utils.env_var_names(provider):
                if env_name not in content:
                    missing.append(
                        f"{path.relative_to(ROOT).as_posix()}:{env_name}"
                    )

    assert missing == []


def test_music_docs_document_expected_provider_credentials():
    providers_page = ROOT / "docs" / "providers.md"
    assert providers_page.exists()

    providers_content = providers_page.read_text(encoding="utf-8")
    missing = []

    for _provider, env_names in env_utils.PROVIDER_ENV_VARS.items():
        for env_name in env_names:
            if env_name not in providers_content:
                missing.append(f"docs/providers.md missing {env_name}")

    for operation, providers in _operation_matrix().items():
        for provider in providers:
            page = DOCS_ROOT / operation / f"{provider}.md"
            content = page.read_text(encoding="utf-8")
            for env_name in env_utils.env_var_names(provider):
                if env_name not in content:
                    missing.append(
                        f"{page.relative_to(ROOT).as_posix()} missing {env_name}"
                    )

    assert missing == []
