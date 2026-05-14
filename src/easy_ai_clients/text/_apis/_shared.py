"""Shared provider metadata and request helpers for text generation wrappers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import requests

from ..post_processing import extrair_request_id, normalizar_uso
from ..pre_processing import (
    _TIMEOUT_PADRAO,
    montar_mensagens_chat,
    obter_chave_api,
    remover_nulos,
    requisicao_json,
)

SNAPSHOT_DATE = "2026-04-25"
ARTIFACT_RUN = "validacao_text_apis_2026-04-25"

OPENAI_CHAT_BASE_PARAMETERS = {
    "model",
    "messages",
    "max_tokens",
    "max_completion_tokens",
    "temperature",
    "top_p",
    "stop",
    "stream",
    "stream_options",
    "tools",
    "tool_choice",
    "response_format",
    "frequency_penalty",
    "presence_penalty",
    "logprobs",
    "top_logprobs",
    "logit_bias",
    "seed",
    "n",
    "user",
    "metadata",
    "parallel_tool_calls",
    "service_tier",
}

OPENAI_RESPONSES_PARAMETERS = {
    "input",
    "instructions",
    "model",
    "include",
    "max_output_tokens",
    "max_tool_calls",
    "metadata",
    "parallel_tool_calls",
    "previous_response_id",
    "prompt_cache_key",
    "prompt_cache_retention",
    "reasoning",
    "safety_identifier",
    "service_tier",
    "store",
    "stream",
    "stream_options",
    "temperature",
    "text",
    "tool_choice",
    "tools",
    "top_p",
    "truncation",
    "conversation",
    "background",
    "user",
}

ANTHROPIC_MESSAGES_PARAMETERS = {
    "model",
    "messages",
    "system",
    "max_tokens",
    "metadata",
    "stop_sequences",
    "stream",
    "temperature",
    "thinking",
    "tool_choice",
    "tools",
    "top_k",
    "top_p",
    "container",
    "context_management",
    "mcp_servers",
    "service_tier",
    "anthropic_beta",
}

GOOGLE_GENERATE_CONTENT_PARAMETERS = {
    "model",
    "contents",
    "tools",
    "toolConfig",
    "safetySettings",
    "systemInstruction",
    "generationConfig",
    "cachedContent",
    "serviceTier",
    "store",
    "stream",
}

COHERE_CHAT_PARAMETERS = {
    "model",
    "messages",
    "stream",
    "temperature",
    "max_tokens",
    "stop_sequences",
    "p",
    "k",
    "frequency_penalty",
    "presence_penalty",
    "tools",
    "tool_choice",
    "strict_tools",
    "response_format",
    "documents",
    "safety_mode",
    "citation_options",
    "connectors",
    "search_queries_only",
    "conversation_id",
    "prompt_truncation",
    "seed",
}

GROQ_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "citation_options",
    "compound_custom",
    "disable_tool_validation",
    "reasoning_effort",
    "reasoning_format",
    "documents",
}

TOGETHER_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "top_k",
    "min_p",
    "repetition_penalty",
    "context_length_exceeded_behavior",
    "safety_model",
    "reasoning_effort",
}

FIREWORKS_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "top_k",
    "min_p",
    "typical_p",
    "repetition_penalty",
    "mirostat_target",
    "mirostat_lr",
    "prompt_cache_key",
    "prompt_cache_isolation_key",
    "raw_output",
    "perf_metrics_in_response",
    "echo",
    "echo_last",
    "ignore_eos",
    "context_length_exceeded_behavior",
    "speculation",
    "prediction",
    "reasoning_effort",
    "reasoning_history",
    "thinking",
    "return_token_ids",
    "functions",
    "function_call",
    "prompt_truncate_len",
    "safe_tokenization",
}

DEEPSEEK_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "thinking",
    "reasoning_effort",
    "prefix",
    "reasoning_content",
}

MISTRAL_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "random_seed",
    "safe_prompt",
    "prediction",
    "prompt_mode",
    "reasoning_effort",
    "guardrails",
}

XAI_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "reasoning_effort",
    "search_parameters",
}

DEEPINFRA_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "top_k",
    "min_p",
    "repetition_penalty",
    "reasoning_effort",
}

HUGGINGFACE_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "tool_prompt",
    "provider",
}

OPENROUTER_PARAMETERS = OPENAI_CHAT_BASE_PARAMETERS | {
    "models",
    "provider",
    "route",
    "plugins",
    "reasoning",
    "cache_control",
    "modalities",
    "image_config",
    "trace",
    "session_id",
    "usage",
}

FAL_PARAMETERS = OPENROUTER_PARAMETERS

KNOWN_PARAMETER_NAMES = (
    OPENAI_CHAT_BASE_PARAMETERS
    | OPENAI_RESPONSES_PARAMETERS
    | ANTHROPIC_MESSAGES_PARAMETERS
    | GOOGLE_GENERATE_CONTENT_PARAMETERS
    | COHERE_CHAT_PARAMETERS
    | GROQ_PARAMETERS
    | TOGETHER_PARAMETERS
    | FIREWORKS_PARAMETERS
    | DEEPSEEK_PARAMETERS
    | MISTRAL_PARAMETERS
    | XAI_PARAMETERS
    | DEEPINFRA_PARAMETERS
    | HUGGINGFACE_PARAMETERS
    | OPENROUTER_PARAMETERS
    | FAL_PARAMETERS
)


@dataclass(frozen=True)
class ProviderSpec:
    """Describe the request surface for one provider wrapper."""

    provider: str
    api: str
    env_var: str
    generation_url: str
    models_url: str
    pricing_url: str
    default_model: str
    supported_parameters: frozenset[str]
    default_max_tokens: int | None = None
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer "
    content_type: str | None = "application/json"
    extra_headers: Mapping[str, str] | None = None


class UnsupportedParameterError(ValueError):
    """Raised when a wrapper receives an unsupported generation parameter."""


class ResponseStub:
    """Minimal response object used for accumulated streaming responses."""

    def __init__(self, headers: Mapping[str, str] | None = None) -> None:
        self.headers = dict(headers or {})


def validate_kwargs(
    *,
    provider: str,
    api: str,
    model: str,
    kwargs: Mapping[str, Any],
    supported_parameters: Iterable[str],
) -> None:
    """Keep the documented kwarg surface available without blocking new provider params."""

    return None


def build_chat_payload(
    *,
    input_text: str,
    instruction: str | None,
    model: str,
    kwargs: Mapping[str, Any],
    default_max_tokens: int | None = None,
) -> dict[str, Any]:
    """Build an OpenAI-compatible chat payload from wrapper inputs and kwargs."""
    payload = {
        "model": model,
        "messages": kwargs.get(
            "messages",
            montar_mensagens_chat(input_text=input_text, instruction=instruction),
        ),
    }
    if default_max_tokens is not None:
        payload["max_tokens"] = default_max_tokens

    for key, value in kwargs.items():
        payload[key] = value

    return remover_nulos(payload)


def execute_chat_request(
    *,
    env_var: str,
    url: str,
    payload: Mapping[str, Any],
    auth_header: str = "Authorization",
    auth_prefix: str = "Bearer ",
    headers_extra: Mapping[str, str] | None = None,
    timeout: int | float | None = None,
) -> tuple[dict[str, Any], Any]:
    """Execute an OpenAI-compatible chat request, accumulating streams."""
    key = obter_chave_api(env_var)
    headers = {"Content-Type": "application/json"}
    if headers_extra:
        headers.update(headers_extra)
    headers[auth_header] = f"{auth_prefix}{key}"

    if payload.get("stream") is True:
        return _execute_openai_chat_stream(
            url=url,
            headers=headers,
            payload=payload,
            timeout=timeout or _TIMEOUT_PADRAO,
        )

    return requisicao_json(
        metodo="POST",
        url=url,
        headers=headers,
        payload=dict(payload),
        timeout=timeout or _TIMEOUT_PADRAO,
    )


def execute_json_request(
    *,
    method: str,
    url: str,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
    timeout: int | float | None = None,
    stream_kind: str | None = None,
    stream: bool = False,
) -> tuple[dict[str, Any], Any]:
    """Execute a JSON request and accumulate known SSE stream formats."""
    should_stream = stream or bool(payload and payload.get("stream") is True)
    if should_stream and stream_kind:
        return _execute_provider_stream(
            url=url,
            headers=headers or {},
            params=params,
            payload=payload,
            timeout=timeout or _TIMEOUT_PADRAO,
            stream_kind=stream_kind,
        )

    return requisicao_json(
        metodo=method,
        url=url,
        headers=dict(headers or {}),
        params=dict(params or {}),
        payload=dict(payload or {}),
        timeout=timeout or _TIMEOUT_PADRAO,
    )


def normalize_reasoning_value(value: Any) -> Any:
    """Convert compact reasoning strings to provider-native objects when useful."""
    if value is None or isinstance(value, Mapping):
        return value
    text = str(value).strip()
    if not text or text.lower() == "none":
        return None
    return {"effort": text}


def _execute_openai_chat_stream(
    *,
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout: int | float,
) -> tuple[dict[str, Any], ResponseStub]:
    chunks, response_headers = _read_sse_json(
        url=url,
        headers=headers,
        params=None,
        payload=payload,
        timeout=timeout,
    )
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    usage: dict[str, Any] = {}
    response_id = None
    response_model = payload.get("model")

    for chunk in chunks:
        response_id = response_id or chunk.get("id")
        response_model = chunk.get("model") or response_model
        if chunk.get("usage"):
            usage = chunk.get("usage") or usage

        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or choice.get("message") or {}
            content = delta.get("content")
            if isinstance(content, str):
                content_parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("text"):
                        content_parts.append(item["text"])
            if delta.get("reasoning_content"):
                reasoning_parts.append(delta["reasoning_content"])

    message = {"role": "assistant", "content": "".join(content_parts)}
    if reasoning_parts:
        message["reasoning_content"] = "".join(reasoning_parts)

    return (
        remover_nulos(
            {
                "id": response_id,
                "model": response_model,
                "object": "chat.completion",
                "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
                "usage": usage or None,
            }
        ),
        ResponseStub(response_headers),
    )


def _execute_provider_stream(
    *,
    url: str,
    headers: Mapping[str, str],
    params: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
    timeout: int | float,
    stream_kind: str,
) -> tuple[dict[str, Any], ResponseStub]:
    chunks, response_headers = _read_sse_json(
        url=url,
        headers=headers,
        params=params,
        payload=payload,
        timeout=timeout,
    )
    if stream_kind == "openai_responses":
        return _accumulate_openai_responses(chunks), ResponseStub(response_headers)
    if stream_kind == "anthropic":
        return _accumulate_anthropic(chunks), ResponseStub(response_headers)
    if stream_kind == "cohere":
        return _accumulate_cohere(chunks), ResponseStub(response_headers)
    if stream_kind == "google":
        return _accumulate_google(chunks), ResponseStub(response_headers)
    return _accumulate_generic_text(chunks), ResponseStub(response_headers)


def _read_sse_json(
    *,
    url: str,
    headers: Mapping[str, str],
    params: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
    timeout: int | float,
) -> tuple[list[dict[str, Any]], Mapping[str, str]]:
    with requests.Session() as session:
        response = session.post(
            url=url,
            headers=dict(headers),
            params=dict(params or {}),
            json=dict(payload),
            timeout=timeout,
            stream=True,
        )
        if not response.ok:
            raise RuntimeError(
                f"Request to `{url}` failed: "
                f"{response.status_code} - {response.text[:1500]}"
            )

        chunks: list[dict[str, Any]] = []
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                item = json.loads(data)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                chunks.append(item)

        return chunks, response.headers


def _accumulate_openai_responses(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    output_parts: list[str] = []
    final_response: dict[str, Any] | None = None
    for chunk in chunks:
        event_type = chunk.get("type")
        if event_type == "response.output_text.delta" and chunk.get("delta"):
            output_parts.append(chunk["delta"])
        if event_type == "response.completed" and isinstance(chunk.get("response"), dict):
            final_response = chunk["response"]

    if final_response:
        if output_parts and not final_response.get("output_text"):
            final_response["output_text"] = "".join(output_parts)
        return final_response

    return {"output_text": "".join(output_parts), "usage": {}}


def _accumulate_anthropic(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    text_parts: list[str] = []
    message: dict[str, Any] = {}
    usage: dict[str, Any] = {}
    for chunk in chunks:
        if chunk.get("type") == "message_start":
            message.update(chunk.get("message") or {})
        if chunk.get("type") == "content_block_delta":
            delta = chunk.get("delta") or {}
            if delta.get("text"):
                text_parts.append(delta["text"])
        if chunk.get("usage"):
            usage.update(chunk.get("usage") or {})

    message.setdefault("content", [{"type": "text", "text": "".join(text_parts)}])
    message["usage"] = usage or message.get("usage") or {}
    return message


def _accumulate_cohere(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    text_parts: list[str] = []
    final: dict[str, Any] | None = None
    for chunk in chunks:
        if chunk.get("type") in {"message-end", "message_end"}:
            final = chunk.get("response") or chunk
        delta = chunk.get("delta") or {}
        message = delta.get("message") if isinstance(delta, dict) else {}
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, dict) and content.get("text"):
            text_parts.append(content["text"])
        if chunk.get("text"):
            text_parts.append(chunk["text"])

    if final:
        return final
    return {
        "message": {"content": [{"type": "text", "text": "".join(text_parts)}]},
        "usage": {},
    }


def _accumulate_google(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    text_parts: list[str] = []
    usage: dict[str, Any] = {}
    for chunk in chunks:
        if chunk.get("usageMetadata"):
            usage = chunk.get("usageMetadata") or usage
        for candidate in chunk.get("candidates") or []:
            content = candidate.get("content") or {}
            for part in content.get("parts") or []:
                if isinstance(part, dict) and part.get("text"):
                    text_parts.append(part["text"])

    return {
        "candidates": [
            {"content": {"role": "model", "parts": [{"text": "".join(text_parts)}]}}
        ],
        "usageMetadata": usage,
    }


def _accumulate_generic_text(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    text_parts: list[str] = []
    usage: dict[str, Any] = {}
    for chunk in chunks:
        if chunk.get("usage"):
            usage = normalizar_uso(chunk.get("usage") or {})
        for key in ("text", "delta", "content"):
            value = chunk.get(key)
            if isinstance(value, str):
                text_parts.append(value)
    return {
        "id": extrair_request_id(chunks[-1]) if chunks else None,
        "choices": [{"message": {"content": "".join(text_parts)}}],
        "usage": usage,
    }
