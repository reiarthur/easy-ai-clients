"""Shared types for image and vision provider integrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict

JsonDict = dict[str, Any]
ImageInput = str
ReferenceImagesInput = list[str]


class ImageOperationResult(TypedDict):
    """Public contract for generate, edit and remix operations."""

    cust_usd: float
    base64: str
    warnings: str
    request_id: str


class AnalyzeOperationResult(TypedDict):
    """Public normalized contract for analyze operations."""

    request_id: str
    cost_usd: float
    input_text: str
    output: str


@dataclass(frozen=True)
class ImageAsset:
    """Normalized in-memory representation of an image input."""

    raw_bytes: bytes
    mime_type: str
    filename: str
    width: int
    height: int
    mode: str
    format_name: str
    source: str
    source_path: Path | None = None


@dataclass(frozen=True)
class PreparedGenerateInputs:
    """Normalized inputs for text-to-image generation."""

    prompt: str


@dataclass(frozen=True)
class PreparedEditInputs:
    """Normalized inputs for image editing."""

    prompt: str
    image: ImageAsset
    mask: ImageAsset | None
    provider_mask_bytes: bytes | None
    provider_mask_mime_type: str | None
    provider_mask_filename: str | None
    preprocess_warnings: str = ""


@dataclass(frozen=True)
class PreparedAnalyzeInputs:
    """Normalized inputs for image-to-text analysis."""

    prompt: str
    image: ImageAsset


@dataclass(frozen=True)
class PreparedRemixInputs:
    """Normalized inputs for text-guided reference image generation."""

    prompt: str
    reference_images: list[ImageAsset]
    base_image: ImageAsset | None


StatusLabel = Literal[
    "passed",
    "blocked_missing_key",
    "blocked_invalid_key",
    "blocked_billing",
    "blocked_moderation",
    "blocked_unsupported",
    "failed_bug",
]
