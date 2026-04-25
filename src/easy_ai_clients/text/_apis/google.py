"""Cliente de geracao texto->texto para a Gemini Developer API.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import (
    atualizar_custo_no_resultado as _atualizar_custo_no_resultado,
)
from ..post_processing import (
    calcular_custo_tokens,
    extrair_request_id,
    extrair_texto_google,
    montar_resultado,
    normalizar_resultado_publico,
    normalizar_uso,
)
from ..pre_processing import (
    obter_chave_api,
    remover_nulos,
    requisicao_json,
)
from ._shared import (
    GOOGLE_GENERATE_CONTENT_PARAMETERS,
    execute_json_request,
    validate_kwargs,
)

_ORCAMENTOS_REASONING = {
    "low": 1024,
    "medium": 4096,
    "high": 8192,
}
_PRECOS_MODELOS = {
    "gemini-3.1-pro-preview": {
        "standard": {
            "ate_200k": {"input": 2.0, "cached_input": 0.20, "output": 12.0},
            "acima_200k": {"input": 4.0, "cached_input": 0.40, "output": 18.0},
        },
        "batch": {
            "ate_200k": {"input": 1.0, "cached_input": 0.20, "output": 6.0},
            "acima_200k": {"input": 2.0, "cached_input": 0.40, "output": 9.0},
        },
        "flex": {
            "ate_200k": {"input": 1.0, "cached_input": 0.20, "output": 6.0},
            "acima_200k": {"input": 2.0, "cached_input": 0.40, "output": 9.0},
        },
        "priority": {
            "ate_200k": {"input": 3.6, "cached_input": 0.36, "output": 21.6},
            "acima_200k": {"input": 7.2, "cached_input": 0.72, "output": 32.4},
        },
    },
    "gemini-3-flash-preview": {
        "standard": {"input": 0.5, "cached_input": 0.05, "output": 3.0},
        "batch": {"input": 0.25, "cached_input": 0.05, "output": 1.5},
        "flex": {"input": 0.25, "cached_input": 0.05, "output": 1.5},
        "priority": {"input": 0.9, "cached_input": 0.09, "output": 5.4},
    },
    "gemini-3.1-flash-lite-preview": {
        "standard": {"input": 0.25, "cached_input": 0.025, "output": 1.5},
        "batch": {"input": 0.125, "cached_input": 0.025, "output": 0.75},
        "flex": {"input": 0.125, "cached_input": 0.025, "output": 0.75},
        "priority": {"input": 0.45, "cached_input": 0.045, "output": 2.7},
    },
    "gemini-2.5-pro": {
        "standard": {
            "ate_200k": {"input": 1.25, "cached_input": 0.125, "output": 10.0},
            "acima_200k": {"input": 2.5, "cached_input": 0.25, "output": 15.0},
        },
        "batch": {
            "ate_200k": {"input": 0.625, "cached_input": 0.125, "output": 5.0},
            "acima_200k": {"input": 1.25, "cached_input": 0.25, "output": 7.5},
        },
        "flex": {
            "ate_200k": {"input": 0.625, "cached_input": 0.125, "output": 5.0},
            "acima_200k": {"input": 1.25, "cached_input": 0.25, "output": 7.5},
        },
        "priority": {
            "ate_200k": {"input": 2.25, "cached_input": 0.225, "output": 18.0},
            "acima_200k": {"input": 4.5, "cached_input": 0.45, "output": 27.0},
        },
    },
    "gemini-2.5-flash": {
        "standard": {"input": 0.30, "cached_input": 0.03, "output": 2.50},
        "batch": {"input": 0.15, "cached_input": 0.03, "output": 1.25},
        "flex": {"input": 0.15, "cached_input": 0.03, "output": 1.25},
        "priority": {"input": 0.54, "cached_input": 0.054, "output": 4.50},
    },
    "gemini-2.5-flash-lite-preview-09-2025": {
        "standard": {"input": 0.10, "cached_input": 0.01, "output": 0.40},
        "batch": {"input": 0.05, "cached_input": 0.01, "output": 0.20},
    },
    "gemini-2.5-flash-lite": {
        "standard": {"input": 0.10, "cached_input": 0.01, "output": 0.40},
        "batch": {"input": 0.05, "cached_input": 0.01, "output": 0.20},
        "flex": {"input": 0.05, "cached_input": 0.01, "output": 0.20},
        "priority": {"input": 0.18, "cached_input": 0.018, "output": 0.72},
    },
    "gemini-2.0-flash": {
        "standard": {"input": 0.10, "cached_input": 0.025, "output": 0.40},
        "batch": {"input": 0.05, "cached_input": 0.025, "output": 0.20},
    },
    "gemini-2.0-flash-lite": {
        "standard": {"input": 0.075, "output": 0.30},
        "batch": {"input": 0.0375, "output": 0.15},
    },
}
_CHAVES_MODELOS_ORDENADAS = sorted(_PRECOS_MODELOS, key=len, reverse=True)


def generate(
    input_text,
    instruction=None,
    model="gemini-2.5-flash-lite",
    **kwargs,
):
    """Generate text with Gemini. Full details: text/docs/google.md."""
    validate_kwargs(
        provider="google",
        api="models.generateContent",
        model=model,
        kwargs=kwargs,
        supported_parameters=GOOGLE_GENERATE_CONTENT_PARAMETERS,
    )
    chave = obter_chave_api("GOOGLE_API_KEY")
    parametros = dict(kwargs)
    stream = parametros.pop("stream", False) is True
    corpo = remover_nulos(
        {
            "contents": parametros.pop("contents", _montar_contents_gemini(input_text)),
            "systemInstruction": parametros.pop(
                "systemInstruction",
                _montar_instruction_gemini(instruction),
            ),
        }
    )
    corpo.update(remover_nulos(parametros))

    action = "streamGenerateContent" if stream else "generateContent"
    params = {"key": chave}
    if stream:
        params["alt"] = "sse"
    resposta_json, resposta_http = execute_json_request(
        method="POST",
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{action}",
        params=params,
        payload=corpo,
        stream_kind="google",
        stream=stream,
    )
    uso = normalizar_uso(resposta_json.get("usageMetadata") or {})
    resultado = montar_resultado(
        provider="google",
        model=model,
        input_text=input_text,
        instruction=instruction,
        output_text=extrair_texto_google(resposta_json),
        request_id=extrair_request_id(resposta_json, resposta_http),
        usage=uso,
        extra={"pricing_mode": _normalizar_service_tier(corpo.get("serviceTier"))},
    )
    custo = _calcular_custo(
        modelo=model,
        uso=uso,
        pricing_mode=_normalizar_service_tier(corpo.get("serviceTier")),
    )
    _atualizar_custo_no_resultado(resultado, custo, origem="usage_x_pricing_page")
    return normalizar_resultado_publico(resultado)


def list_models(api_key=None, timeout=180):
    """Lista os modelos Gemini disponiveis para `generateContent`."""
    chave = obter_chave_api("GOOGLE_API_KEY", api_key=api_key)
    resposta_json, _ = requisicao_json(
        metodo="GET",
        url="https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": chave},
        timeout=timeout,
    )
    modelos = resposta_json.get("models") or []
    return [
        item
        for item in modelos
        if "generateContent" in (item.get("supportedGenerationMethods") or [])
    ]


def _montar_instruction_gemini(instruction):
    """Converte a instrucao de sistema para o formato do Gemini."""
    if not instruction:
        return None
    return {"parts": [{"text": instruction}]}


def _montar_contents_gemini(input_text):
    """Converte o texto principal no formato minimo exigido pelo Gemini."""
    return [{"role": "user", "parts": [{"text": input_text}]}]


def _calcular_custo(modelo, uso, pricing_mode="standard"):
    """Calcula custo a partir do uso do Gemini e da tabela publica."""
    tabela = _resolver_tabela_precos(modelo, uso, pricing_mode=pricing_mode)
    if not tabela:
        return 0.0
    return calcular_custo_tokens(uso, tabela)


def _resolver_tabela_precos(modelo, uso, pricing_mode="standard"):
    """Resolve a tabela de precos conforme modelo, tier e tamanho do prompt."""
    modelo_normalizado = (modelo or "").lower()
    tier = (pricing_mode or "standard").lower()

    for chave in _CHAVES_MODELOS_ORDENADAS:
        if chave not in modelo_normalizado:
            continue

        precos = _PRECOS_MODELOS[chave]
        tabela_tier = precos.get(tier) or precos.get("standard")
        if "ate_200k" in tabela_tier:
            input_tokens = (uso or {}).get("input_tokens", 0) or 0
            faixa = "acima_200k" if input_tokens > 200000 else "ate_200k"
            return tabela_tier.get(faixa)

        return tabela_tier

    return None


def _montar_thinking_config(modelo, reasoning):
    """Monta o bloco `thinkingConfig` a partir do nivel simplificado."""
    nivel = _normalizar_reasoning(reasoning)
    if not nivel or not _modelo_suporta_reasoning(modelo):
        return None
    return {"thinkingBudget": _ORCAMENTOS_REASONING[nivel]}


def _normalizar_reasoning(reasoning):
    """Normaliza o nivel de reasoning exposto pelo wrapper."""
    if reasoning is None:
        return None
    reasoning = str(reasoning).strip().lower()
    if not reasoning or reasoning == "none":
        return None
    if reasoning in _ORCAMENTOS_REASONING:
        return reasoning
    raise ValueError("`reasoning` must be one of: low, medium, high, none, or None.")


def _modelo_suporta_reasoning(modelo):
    """Retorna se o wrapper deve enviar `thinkingConfig` para o modelo."""
    modelo_normalizado = (modelo or "").lower()
    return modelo_normalizado.startswith("gemini-2.5") or modelo_normalizado.startswith(
        "gemini-3"
    )


def _normalizar_service_tier(service_tier):
    """Normaliza o tier usado para a tabela local de custo."""
    if service_tier is None:
        return "standard"
    service_tier = str(service_tier).strip().lower()
    if not service_tier or service_tier == "none":
        return "standard"
    return service_tier
