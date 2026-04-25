"""Image parsing and normalization helpers."""

from __future__ import annotations

import base64
import binascii
import io
import re
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageOps

from .errors import InputValidationError
from .http_utils import download_response
from .types import ImageAsset

_DATA_URL_RE = re.compile(
    r"^data:(?P<mime>[-\w.+/]+)?;base64,(?P<data>[A-Za-z0-9+/=\s]+)$",
    re.IGNORECASE,
)
_ALLOWED_IMAGE_URL_SCHEMES = {"http", "https"}
_GENERIC_IMAGE_CONTENT_TYPES = {
    "application/octet-stream",
    "binary/octet-stream",
}


def _read_image_asset(raw_bytes: bytes, *, filename: str, source: str) -> ImageAsset:
    try:
        with Image.open(io.BytesIO(raw_bytes)) as image:
            image.load()
            format_name = (image.format or "PNG").upper()
            mime_type = Image.MIME.get(format_name, "image/png")
            return ImageAsset(
                raw_bytes=raw_bytes,
                mime_type=mime_type,
                filename=filename,
                width=image.width,
                height=image.height,
                mode=image.mode,
                format_name=format_name,
                source=source,
            )
    except Exception as exc:  # pragma: no cover - Pillow error variants are broad
        raise InputValidationError(f"{source} is not a supported image.") from exc


def _looks_like_public_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return bool(parsed.scheme and parsed.netloc)


def _filename_from_url(value: str, *, field_name: str) -> str:
    parsed = urlparse(value)
    name = Path(parsed.path).name
    return name or f"{field_name}.png"


def _read_public_url_image(
    value: str,
    *,
    field_name: str,
    timeout_seconds: int,
) -> ImageAsset:
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() not in _ALLOWED_IMAGE_URL_SCHEMES:
        allowed = ", ".join(sorted(_ALLOWED_IMAGE_URL_SCHEMES))
        raise InputValidationError(f"{field_name} URL scheme must be one of: {allowed}.")

    response = download_response(
        value.strip(),
        headers={"Accept": "image/*"},
        timeout_seconds=timeout_seconds,
    )
    content_type = (response.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    if content_type and not (
        content_type.startswith("image/") or content_type in _GENERIC_IMAGE_CONTENT_TYPES
    ):
        raise InputValidationError(
            f"{field_name} URL returned content type `{content_type}`, not an image."
        )
    return _read_image_asset(
        response.content,
        filename=_filename_from_url(value, field_name=field_name),
        source=value.strip(),
    )


def load_image_input(value: str, *, field_name: str, timeout_seconds: int = 30) -> ImageAsset:
    """Normalize a public image input into an :class:`ImageAsset`.

    The public contract across `generate`, `edit`, `analyze`, and `remix`
    accepts image values as:

    - absolute or relative file paths;
    - public `http` or `https` image URLs;
    - raw base64 strings containing only image bytes;
    - base64 data URLs such as `data:image/png;base64,...`.

    Resolution order is intentionally stable:

    1. Treat the value as a file path if it points to an existing file.
    2. Otherwise parse it as a data URL.
    3. Otherwise download it as a public image URL when it has an URL shape.
    4. Otherwise parse it as raw base64.

    Args:
        value: Public image input value.
        field_name: Human-readable parameter name used in validation messages.
        timeout_seconds: Timeout for public image URL downloads.

    Returns:
        Parsed :class:`ImageAsset` with raw bytes, dimensions, MIME type, format,
        and source metadata.

    Raises:
        InputValidationError: If the value is neither a readable file path nor a
            decodable image payload.
    """

    candidate_path = Path(value)
    try:
        path_exists = candidate_path.exists() and candidate_path.is_file()
    except OSError:
        path_exists = False
    if path_exists:
        raw_bytes = candidate_path.read_bytes()
        asset = _read_image_asset(
            raw_bytes,
            filename=candidate_path.name,
            source=str(candidate_path.resolve()),
        )
        return ImageAsset(**{**asset.__dict__, "source_path": candidate_path.resolve()})

    match = _DATA_URL_RE.match(value.strip())
    if match:
        raw_bytes = base64.b64decode(match.group("data"), validate=False)
        filename = f"{field_name}.{match.group('mime').split('/')[-1]}"
        return _read_image_asset(raw_bytes, filename=filename, source=f"{field_name}:data-url")

    if _looks_like_public_url(value):
        return _read_public_url_image(
            value,
            field_name=field_name,
            timeout_seconds=timeout_seconds,
        )

    try:
        raw_bytes = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InputValidationError(
            f"{field_name} must be a valid file path, public image URL, raw base64 image or data URL."
        ) from exc
    return _read_image_asset(raw_bytes, filename=f"{field_name}.png", source=f"{field_name}:base64")


def load_image_inputs(values: str | Iterable[str], *, field_name: str) -> list[ImageAsset]:
    """Normalize one or many public image inputs into a non-empty asset list.

    Args:
        values: Either a single public image string or an iterable of them.
        field_name: Base parameter name used in validation messages.

    Returns:
        List of normalized :class:`ImageAsset` objects.

    Raises:
        InputValidationError: If the iterable is empty or any item cannot be
            normalized safely.
    """

    if isinstance(values, str):
        return [load_image_input(values, field_name=field_name)]
    assets: list[ImageAsset] = []
    for index, value in enumerate(values, start=1):
        assets.append(load_image_input(value, field_name=f"{field_name}[{index}]"))
    if not assets:
        raise InputValidationError(f"{field_name} must contain at least one image.")
    return assets


def image_to_png_bytes(asset: ImageAsset, *, force_mode: str | None = None) -> bytes:
    """Re-encode an image asset as PNG bytes.

    Args:
        asset: Source image asset.
        force_mode: Optional Pillow mode such as `RGB`, `RGBA`, or `L`. When not
            provided, the helper preserves alpha where possible and normalizes
            exotic modes to a PNG-safe mode.

    Returns:
        PNG-encoded bytes ready for multipart upload or base64 conversion.
    """

    with Image.open(io.BytesIO(asset.raw_bytes)) as image:
        image.load()
        if force_mode:
            image = image.convert(force_mode)
        elif image.mode not in {"RGB", "RGBA", "L", "LA"}:
            image = image.convert("RGBA" if "A" in image.mode else "RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


def image_to_base64(asset: ImageAsset, *, force_png: bool = True) -> str:
    """Convert an image asset into pure base64 text.

    Args:
        asset: Source image asset.
        force_png: When `True`, normalize to PNG before encoding so callers get
            deterministic output bytes regardless of the original format.

    Returns:
        Base64 string without any `data:` prefix.
    """

    raw_bytes = image_to_png_bytes(asset) if force_png else asset.raw_bytes
    return base64.b64encode(raw_bytes).decode("ascii")


def image_to_data_url(asset: ImageAsset, *, force_png: bool = True) -> str:
    """Convert an image asset into a base64 data URL.

    Args:
        asset: Source image asset.
        force_png: When `True`, normalize the payload to PNG and emit
            `data:image/png;base64,...`.

    Returns:
        Data URL suitable for providers that accept image URLs or inline image
        content but not multipart uploads.
    """

    raw_bytes = image_to_png_bytes(asset) if force_png else asset.raw_bytes
    mime_type = "image/png" if force_png else asset.mime_type
    return f"data:{mime_type};base64,{base64.b64encode(raw_bytes).decode('ascii')}"


def _resize_mask_to_match(mask: Image.Image, *, width: int, height: int) -> Image.Image:
    if mask.size == (width, height):
        return mask
    return mask.resize((width, height), Image.Resampling.NEAREST)


def normalize_public_mask_asset(
    mask: ImageAsset,
    *,
    width: int,
    height: int,
    threshold: int = 128,
) -> tuple[ImageAsset, str]:
    """Normalize a public mask to strict black-and-white PNG bytes.

    The public edit contract for this repository is always:
        black pixels -> editable region
        white pixels -> protected region

    This helper makes that contract explicit by resizing the incoming mask with
    nearest-neighbor sampling, preserving spatial alignment with the source
    image, and then thresholding any non-binary grayscale values into pure black
    or white. A warning string is returned whenever resizing and/or binarization
    was necessary so higher layers can surface the normalization that happened.

    Args:
        mask: Public mask asset, typically produced by :func:`load_image_input`.
        width: Required output width, usually matching the edited image width.
        height: Required output height, usually matching the edited image height.
        threshold: Threshold used to binarize grayscale values. Values below the
            threshold become black/editable; values at or above it become
            white/protected.

    Returns:
        Tuple `(normalized_mask_asset, warning_text)`. The returned asset is a
        PNG mask guaranteed to contain only `0` and `255` luminance values.
    """

    with Image.open(io.BytesIO(mask.raw_bytes)) as image:
        image.load()
        grayscale = ImageOps.grayscale(image)
        resized = _resize_mask_to_match(grayscale, width=width, height=height)
        needs_resize = resized.size != grayscale.size
        histogram = resized.histogram()
        non_binary_pixels = sum(
            count for value, count in enumerate(histogram) if value not in (0, 255)
        )
        needs_binarize = non_binary_pixels > 0
        binary = resized.point(lambda value: 0 if value < threshold else 255, mode="L")
        buffer = io.BytesIO()
        binary.save(buffer, format="PNG")

    warning_parts: list[str] = []
    if needs_resize:
        warning_parts.append(
            "Mask was resized with nearest-neighbor sampling to match the input image size."
        )
    if needs_binarize:
        warning_parts.append(
            "Mask contained non-binary pixel values and was thresholded at 128 to enforce the public black-editable/white-protected contract."
        )

    normalized = _read_image_asset(
        buffer.getvalue(),
        filename="mask.normalized.png",
        source=f"{mask.source}:normalized",
    )
    source_path = mask.source_path if mask.source_path and mask.source_path.exists() else None
    return (
        ImageAsset(**{**normalized.__dict__, "source_path": source_path}),
        "; ".join(warning_parts),
    )


def public_mask_to_openai(mask: ImageAsset, *, width: int, height: int) -> bytes:
    """Convert the public mask contract into OpenAI's alpha-mask payload.

    OpenAI Images treats transparent pixels as editable and opaque pixels as
    preserved. The public contract of this repository is the inverse visual
    language most users expect from paint tools, so this helper first normalizes
    the public mask to strict black/white and then writes that grayscale image
    into the alpha channel of an RGBA PNG.

    Args:
        mask: Public mask asset.
        width: Target width expected by OpenAI.
        height: Target height expected by OpenAI.

    Returns:
        PNG bytes whose alpha channel encodes the editable region.
    """

    normalized_mask, _ = normalize_public_mask_asset(mask, width=width, height=height)
    with Image.open(io.BytesIO(normalized_mask.raw_bytes)) as image:
        image.load()
        alpha = ImageOps.grayscale(image)
        rgba = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        rgba.putalpha(alpha)
        buffer = io.BytesIO()
        rgba.save(buffer, format="PNG")
        return buffer.getvalue()


def public_mask_to_bfl_fill(mask: ImageAsset, *, width: int, height: int) -> bytes:
    """Convert public mask to BFL Fill mask.

    Public contract:
        black = editable
        white = protected

    BFL Fill contract:
        white = inpaint
        black = preserve

    Args:
        mask: Public mask asset.
        width: Target width required by FLUX.1 Fill.
        height: Target height required by FLUX.1 Fill.

    Returns:
        PNG bytes in BFL Fill polarity.
    """

    normalized_mask, _ = normalize_public_mask_asset(mask, width=width, height=height)
    with Image.open(io.BytesIO(normalized_mask.raw_bytes)) as image:
        image.load()
        inverted = ImageOps.invert(ImageOps.grayscale(image))
        buffer = io.BytesIO()
        inverted.save(buffer, format="PNG")
        return buffer.getvalue()


def public_mask_to_stability(mask: ImageAsset, *, width: int, height: int) -> bytes:
    """Convert the public mask contract into Stability's effective inpaint mask.

    The public layer remains `black = editable`, `white = protected`. This
    helper converts that contract into the grayscale polarity currently used by
    the Stability inpaint path exercised by this repository, based on the
    project's real integration tests. The mask is normalized to binary PNG first
    so all callers send a deterministic payload.

    Args:
        mask: Public mask asset.
        width: Target width required by the Stability request.
        height: Target height required by the Stability request.

    Returns:
        PNG bytes in the provider-specific grayscale polarity expected by the
        current wrapper implementation.
    """

    normalized_mask, _ = normalize_public_mask_asset(mask, width=width, height=height)
    with Image.open(io.BytesIO(normalized_mask.raw_bytes)) as image:
        image.load()
        grayscale = ImageOps.invert(ImageOps.grayscale(image))
        buffer = io.BytesIO()
        grayscale.save(buffer, format="PNG")
        return buffer.getvalue()


def full_editable_mask(*, width: int, height: int) -> bytes:
    """Return a full-black public mask meaning the entire image is editable.

    Args:
        width: Mask width.
        height: Mask height.

    Returns:
        PNG bytes following the public contract of this repository.
    """

    mask = Image.new("L", (width, height), color=0)
    buffer = io.BytesIO()
    mask.save(buffer, format="PNG")
    return buffer.getvalue()


def multipart_image(
    field_name: str,
    raw_bytes: bytes,
    *,
    filename: str,
    mime_type: str,
) -> tuple[str, tuple[str, bytes, str]]:
    """Build an `httpx`-compatible multipart file tuple.

    Args:
        field_name: Multipart field name expected by the provider.
        raw_bytes: File content.
        filename: Filename reported to the provider.
        mime_type: Declared MIME type.

    Returns:
        Tuple in the exact shape accepted by `httpx.Client.request(..., files=...)`.
    """

    return (field_name, (filename, raw_bytes, mime_type))
