"""Helpers de custo com aritmética exata em `Decimal`.

Última atualização: 2026-04-23
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .types import JsonDict

MICRO = Decimal("1000000")
USD_TICKS = Decimal("10000000000")

OPENAI_TEXT_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
    "gpt-4.1-nano": (Decimal("0.10"), Decimal("0.40")),
    "gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")),
    "gpt-5-nano": (Decimal("0.05"), Decimal("0.40")),
}

GROQ_TEXT_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "meta-llama/llama-4-scout-17b-16e-instruct": (
        Decimal("0.11"),
        Decimal("0.34"),
    )
}

ANTHROPIC_TEXT_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "claude-3-5-haiku-20241022": (Decimal("0.80"), Decimal("4.00")),
    "claude-haiku-4-5-20251001": (Decimal("1.00"), Decimal("5.00")),
    "claude-haiku-4-5": (Decimal("1.00"), Decimal("5.00")),
}

FIREWORKS_TEXT_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "accounts/fireworks/models/qwen3-vl-30b-a3b-instruct": (
        Decimal("0.15"),
        Decimal("0.60"),
    )
}

GEMINI_TEXT_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "gemini-2.5-flash-lite": (Decimal("0.10"), Decimal("0.40")),
    "gemini-2.5-flash": (Decimal("0.30"), Decimal("2.50"))
}

OPENAI_IMAGE_RATES: dict[str, dict[str, Decimal | None]] = {
    "gpt-image-2": {
        "text_input": Decimal("5.00"),
        "text_cached_input": Decimal("1.25"),
        "text_output": None,
        "image_input": Decimal("8.00"),
        "image_cached_input": Decimal("2.00"),
        "image_output": Decimal("30.00"),
    },
    "gpt-image-2-2026-04-21": {
        "text_input": Decimal("5.00"),
        "text_cached_input": Decimal("1.25"),
        "text_output": None,
        "image_input": Decimal("8.00"),
        "image_cached_input": Decimal("2.00"),
        "image_output": Decimal("30.00"),
    },
    "gpt-image-1.5": {
        "text_input": Decimal("5.00"),
        "text_cached_input": Decimal("1.25"),
        "text_output": Decimal("10.00"),
        "image_input": Decimal("8.00"),
        "image_cached_input": Decimal("2.00"),
        "image_output": Decimal("32.00"),
    },
    "chatgpt-image-latest": {
        "text_input": Decimal("5.00"),
        "text_cached_input": Decimal("1.25"),
        "text_output": Decimal("10.00"),
        "image_input": Decimal("8.00"),
        "image_cached_input": Decimal("2.00"),
        "image_output": Decimal("32.00"),
    },
    "gpt-image-1": {
        "text_input": Decimal("5.00"),
        "text_cached_input": Decimal("1.25"),
        "text_output": None,
        "image_input": Decimal("10.00"),
        "image_cached_input": Decimal("2.50"),
        "image_output": Decimal("40.00"),
    },
    "gpt-image-1-mini": {
        "text_input": Decimal("2.00"),
        "text_cached_input": Decimal("0.20"),
        "text_output": None,
        "image_input": Decimal("2.50"),
        "image_cached_input": Decimal("0.25"),
        "image_output": Decimal("8.00"),
    },
}

OPENAI_DALLE_IMAGE_PRICES: dict[str, dict[str, Decimal]] = {
    "dall-e-2": {
        "1024x1024": Decimal("0.016"),
        "1024x1536": Decimal("0.018"),
        "1536x1024": Decimal("0.020"),
    },
    "dall-e-3:standard": {
        "1024x1024": Decimal("0.040"),
        "1024x1536": Decimal("0.080"),
        "1536x1024": Decimal("0.080"),
    },
    "dall-e-3:hd": {
        "1024x1024": Decimal("0.080"),
        "1024x1536": Decimal("0.120"),
        "1536x1024": Decimal("0.120"),
    },
}

GEMINI_IMAGE_RATES: dict[str, dict[str, Decimal | None]] = {
    "gemini-2.5-flash-image": {
        "input": Decimal("0.30"),
        "output_text": Decimal("2.50"),
        "output_image": Decimal("30.00"),
    },
    "gemini-3.1-flash-image-preview": {
        "input": Decimal("0.25"),
        "output_text": None,
        "output_image": Decimal("60.00"),
    },
    "gemini-3-pro-image-preview": {
        "input": Decimal("2.00"),
        "output_text": Decimal("12.00"),
        "output_image": Decimal("120.00"),
    },
    "nano-banana-pro-preview": {
        "input": Decimal("2.00"),
        "output_text": Decimal("12.00"),
        "output_image": Decimal("120.00"),
    },
}


def decimal_from(value: Any, *, default: Decimal = Decimal("0")) -> Decimal:
    """Convert arbitrary numeric input into :class:`Decimal` safely.

    Args:
        value: Integer, float, string, Decimal, or `None`.
        default: Fallback decimal used when conversion is not possible.

    Returns:
        Parsed :class:`Decimal`, or `default` if the value is empty or invalid.
    """

    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def decimal_to_float(value: Decimal | float | int) -> float:
    """Convert internal money values to the public `float` contract.

    The public wrappers always expose `cust_usd` as `float`, even when internal
    calculations use `Decimal` for precision.

    Args:
        value: Decimal or numeric value.

    Returns:
        Plain Python `float`.
    """

    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def cost_from_usage(
    *,
    input_tokens: int | Decimal = 0,
    output_tokens: int | Decimal = 0,
    input_rate_per_million: Decimal,
    output_rate_per_million: Decimal,
    cached_input_tokens: int | Decimal = 0,
    cached_input_rate_per_million: Decimal | None = None,
) -> Decimal:
    """Calculate USD cost from token usage and per-million-token rates.

    Args:
        input_tokens: Billable prompt/input token count.
        output_tokens: Billable completion/output token count.
        input_rate_per_million: USD rate per one million input tokens.
        output_rate_per_million: USD rate per one million output tokens.
        cached_input_tokens: Prompt tokens billed at a reduced cache rate.
        cached_input_rate_per_million: Optional cache-hit input rate.

    Returns:
        Exact :class:`Decimal` USD value.
    """

    total = (decimal_from(input_tokens) * input_rate_per_million) / MICRO
    total += (decimal_from(output_tokens) * output_rate_per_million) / MICRO
    if cached_input_rate_per_million is not None:
        total += (decimal_from(cached_input_tokens) * cached_input_rate_per_million) / MICRO
    return total


def extract_openai_usage_cost(model: str, usage: JsonDict | None) -> Decimal | None:
    """Calculate exact OpenAI text/vision cost when usage fields are available.

    Args:
        model: OpenAI model id.
        usage: Usage block returned by the provider.

    Returns:
        Exact USD cost when both the model pricing and usage fields are known,
        otherwise `None`.
    """

    if not usage or model not in OPENAI_TEXT_RATES:
        return None
    input_rate, output_rate = OPENAI_TEXT_RATES[model]
    prompt_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    output_tokens = int(
        usage.get("output_tokens")
        or usage.get("completion_tokens")
        or usage.get("output_text_tokens")
        or 0
    )
    cached_tokens = int(
        usage.get("input_tokens_details", {}).get("cached_tokens")
        or usage.get("prompt_tokens_details", {}).get("cached_tokens")
        or 0
    )
    cache_rate = input_rate / Decimal("10")
    return cost_from_usage(
        input_tokens=prompt_tokens,
        output_tokens=output_tokens,
        input_rate_per_million=input_rate,
        output_rate_per_million=output_rate,
        cached_input_tokens=cached_tokens,
        cached_input_rate_per_million=cache_rate,
    )


def extract_openai_image_usage_cost(model: str, usage: JsonDict | None) -> Decimal | None:
    """Calcula o custo exato de geração/edição de imagem da OpenAI.

    ### Parâmetros:
        model: Identificador do modelo de imagem da OpenAI.
        usage: Bloco `usage` retornado pelo endpoint `/images/*`.

    ### Retorna:
        Custo exato em USD quando o modelo e o bloco `usage` suportam cálculo
        determinístico; caso contrário, `None`.
    """

    rates = OPENAI_IMAGE_RATES.get(model)
    if not usage or rates is None:
        return None

    input_details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}

    input_text_tokens = int(input_details.get("text_tokens") or 0)
    input_image_tokens = int(input_details.get("image_tokens") or 0)
    cached_text_tokens = int(input_details.get("cached_text_tokens") or 0)
    cached_image_tokens = int(input_details.get("cached_image_tokens") or 0)

    output_text_tokens = int(output_details.get("text_tokens") or 0)
    output_image_tokens = int(output_details.get("image_tokens") or 0)

    if not (input_text_tokens or input_image_tokens):
        input_text_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    if not (output_text_tokens or output_image_tokens):
        output_image_tokens = int(
            usage.get("output_tokens")
            or usage.get("completion_tokens")
            or 0
        )

    text_output_rate = rates.get("text_output")
    if output_text_tokens and text_output_rate is None:
        return None

    total = Decimal("0")
    total += cost_from_usage(
        input_tokens=input_text_tokens,
        output_tokens=output_text_tokens,
        input_rate_per_million=decimal_from(rates["text_input"]),
        output_rate_per_million=decimal_from(text_output_rate),
        cached_input_tokens=cached_text_tokens,
        cached_input_rate_per_million=decimal_from(rates["text_cached_input"]),
    )
    total += cost_from_usage(
        input_tokens=input_image_tokens,
        output_tokens=output_image_tokens,
        input_rate_per_million=decimal_from(rates["image_input"]),
        output_rate_per_million=decimal_from(rates["image_output"]),
        cached_input_tokens=cached_image_tokens,
        cached_input_rate_per_million=decimal_from(rates["image_cached_input"]),
    )
    return total


def get_openai_dalle_image_price(model: str, size: str, quality: str) -> Decimal | None:
    """Retorna o preço fixo por imagem dos modelos DALL·E suportados."""

    normalized_model = (model or "").strip().lower()
    normalized_size = (size or "").strip().lower()
    normalized_quality = (quality or "").strip().lower()
    if normalized_model == "dall-e-2":
        table_key = "dall-e-2"
    elif normalized_model == "dall-e-3":
        quality_key = "hd" if normalized_quality in {"hd", "high"} else "standard"
        table_key = f"dall-e-3:{quality_key}"
    else:
        return None
    return OPENAI_DALLE_IMAGE_PRICES.get(table_key, {}).get(normalized_size)


def extract_groq_usage_cost(model: str, usage: JsonDict | None) -> Decimal | None:
    """Calculate exact Groq cost for priced analyze models.

    Args:
        model: Groq model id.
        usage: Usage block from the response.

    Returns:
        Exact USD cost or `None` when pricing cannot be derived safely.
    """

    if not usage or model not in GROQ_TEXT_RATES:
        return None
    input_rate, output_rate = GROQ_TEXT_RATES[model]
    return cost_from_usage(
        input_tokens=int(usage.get("prompt_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or 0),
        input_rate_per_million=input_rate,
        output_rate_per_million=output_rate,
    )


def extract_anthropic_usage_cost(model: str, usage: JsonDict | None) -> Decimal | None:
    """Calculate exact Anthropic Messages API cost for known models.

    Args:
        model: Claude model id or alias present in `ANTHROPIC_TEXT_RATES`.
        usage: Anthropic `usage` object containing input/output token counts.

    Returns:
        Exact USD cost or `None` when either the model or usage data is missing.
    """

    if not usage or model not in ANTHROPIC_TEXT_RATES:
        return None
    input_rate, output_rate = ANTHROPIC_TEXT_RATES[model]
    return cost_from_usage(
        input_tokens=int(usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("output_tokens") or 0),
        input_rate_per_million=input_rate,
        output_rate_per_million=output_rate,
    )


def extract_fireworks_usage_cost(model: str, usage: JsonDict | None) -> Decimal | None:
    """Calculate Fireworks analyze cost when public pricing is known.

    Args:
        model: Fireworks model id.
        usage: Response usage block.

    Returns:
        Exact USD cost or `None` when the model is not in the local pricing map
        or usage is absent.
    """

    if not usage or model not in FIREWORKS_TEXT_RATES:
        return None
    input_rate, output_rate = FIREWORKS_TEXT_RATES[model]
    return cost_from_usage(
        input_tokens=int(usage.get("prompt_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or 0),
        input_rate_per_million=input_rate,
        output_rate_per_million=output_rate,
    )


def extract_gemini_usage_cost(model: str, usage: JsonDict | None) -> Decimal | None:
    """Calculate Gemini analyze cost from usage metadata and local pricing.

    Args:
        model: Gemini model id.
        usage: Gemini `usageMetadata` object.

    Returns:
        Exact USD cost when the model and usage metadata are both supported,
        otherwise `None`.
    """

    if not usage or model not in GEMINI_TEXT_RATES:
        return None
    input_rate, output_rate = GEMINI_TEXT_RATES[model]
    prompt_tokens = int(usage.get("promptTokenCount") or 0)
    output_tokens = int(usage.get("candidatesTokenCount") or 0)
    cached_tokens = int(usage.get("cachedContentTokenCount") or 0)
    return cost_from_usage(
        input_tokens=prompt_tokens,
        output_tokens=output_tokens,
        input_rate_per_million=input_rate,
        output_rate_per_million=output_rate,
        cached_input_tokens=cached_tokens,
        cached_input_rate_per_million=Decimal("0.03"),
    )


def extract_gemini_image_usage_cost(model: str, usage: JsonDict | None) -> Decimal | None:
    """Calcula o custo exato de geração/edição/remix de imagem do Gemini."""

    rates = GEMINI_IMAGE_RATES.get(model)
    if not usage or rates is None:
        return None

    prompt_tokens = int(usage.get("promptTokenCount") or 0)
    output_details = usage.get("candidatesTokensDetails") or []

    output_text_tokens = 0
    output_image_tokens = 0
    if isinstance(output_details, list):
        for detail in output_details:
            if not isinstance(detail, dict):
                continue
            modality = str(detail.get("modality") or "").upper()
            tokens = int(detail.get("tokenCount") or 0)
            if modality == "TEXT":
                output_text_tokens += tokens
            elif modality == "IMAGE":
                output_image_tokens += tokens

    if not (output_text_tokens or output_image_tokens):
        output_image_tokens = int(usage.get("candidatesTokenCount") or 0)

    output_text_rate = rates.get("output_text")
    if output_text_tokens and output_text_rate is None:
        return None

    total = Decimal("0")
    total += cost_from_usage(
        input_tokens=prompt_tokens,
        output_tokens=output_text_tokens,
        input_rate_per_million=decimal_from(rates["input"]),
        output_rate_per_million=decimal_from(output_text_rate),
    )
    total += cost_from_usage(
        output_tokens=output_image_tokens,
        input_rate_per_million=Decimal("0"),
        output_rate_per_million=decimal_from(rates["output_image"]),
    )
    return total


def usd_ticks_to_decimal(value: Any) -> Decimal | None:
    """Convert xAI USD ticks to Decimal USD.

    xAI documents `cost_in_usd_ticks` as 1/10,000,000,000 USD.

    Args:
        value: xAI `cost_in_usd_ticks` integer or numeric string.

    Returns:
        Decimal USD cost, or `None` when the provider did not expose tick usage.
    """

    if value is None:
        return None
    return decimal_from(value) / USD_TICKS
