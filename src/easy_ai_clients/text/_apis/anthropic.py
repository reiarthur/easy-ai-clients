"""Cliente de geracao texto->texto para a Messages API da Anthropic.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import (
    atualizar_custo_no_resultado as _atualizar_custo_no_resultado,
)
from ..post_processing import (
    calcular_custo_tokens,
    extrair_request_id,
    extrair_texto_anthropic,
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
    ANTHROPIC_MESSAGES_PARAMETERS,
    execute_json_request,
    validate_kwargs,
)

_MAX_TOKENS_PADRAO = 256
_ORCAMENTOS_REASONING = {
    "low": 1024,
    "medium": 4096,
    "high": 8192,
}
_PRECOS_MODELOS = {
    "claude-opus-4-7": {
        "input": 5.0,
        "output": 25.0,
        "cache_write_5m": 6.25,
        "cache_write_1h": 10.0,
        "cache_read": 0.5,
    },
    "claude-opus-4-6": {
        "input": 5.0,
        "output": 25.0,
        "cache_write_5m": 6.25,
        "cache_write_1h": 10.0,
        "cache_read": 0.5,
    },
    "claude-opus-4-5": {
        "input": 5.0,
        "output": 25.0,
        "cache_write_5m": 6.25,
        "cache_write_1h": 10.0,
        "cache_read": 0.5,
    },
    "claude-opus-4-1": {
        "input": 15.0,
        "output": 75.0,
        "cache_write_5m": 18.75,
        "cache_write_1h": 30.0,
        "cache_read": 1.5,
    },
    "claude-opus-4": {
        "input": 15.0,
        "output": 75.0,
        "cache_write_5m": 18.75,
        "cache_write_1h": 30.0,
        "cache_read": 1.5,
    },
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_write_5m": 3.75,
        "cache_write_1h": 6.0,
        "cache_read": 0.3,
    },
    "claude-sonnet-4-5": {
        "input": 3.0,
        "output": 15.0,
        "cache_write_5m": 3.75,
        "cache_write_1h": 6.0,
        "cache_read": 0.3,
    },
    "claude-sonnet-4": {
        "input": 3.0,
        "output": 15.0,
        "cache_write_5m": 3.75,
        "cache_write_1h": 6.0,
        "cache_read": 0.3,
    },
    "claude-haiku-4-5": {
        "input": 1.0,
        "output": 5.0,
        "cache_write_5m": 1.25,
        "cache_write_1h": 2.0,
        "cache_read": 0.1,
    },
    "claude-haiku-3.5": {
        "input": 0.8,
        "output": 4.0,
        "cache_write_5m": 1.0,
        "cache_write_1h": 1.6,
        "cache_read": 0.08,
    },
    "claude-haiku-3": {
        "input": 0.25,
        "output": 1.25,
        "cache_write_5m": 0.3,
        "cache_write_1h": 0.5,
        "cache_read": 0.03,
    },
}


def generate(
    input_text,
    instruction=None,
    model="claude-haiku-4-5-20251001",
    **kwargs,
):
    """Generate text with Anthropic Messages. Full details: text/docs/anthropic.md."""
    validate_kwargs(
        provider="anthropic",
        api="messages",
        model=model,
        kwargs=kwargs,
        supported_parameters=ANTHROPIC_MESSAGES_PARAMETERS,
    )
    chave = obter_chave_api("ANTHROPIC_API_KEY")
    parametros = dict(kwargs)
    anthropic_beta = parametros.pop("anthropic_beta", None)
    parametros.setdefault("max_tokens", _MAX_TOKENS_PADRAO)
    corpo = remover_nulos(
        {
            "model": model,
            "system": instruction,
            "messages": _montar_mensagens_anthropic(input_text),
        }
    )
    corpo.update(remover_nulos(parametros))

    headers = {
        "x-api-key": chave,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    if anthropic_beta:
        headers["anthropic-beta"] = str(anthropic_beta)

    resposta_json, resposta_http = execute_json_request(
        method="POST",
        url="https://api.anthropic.com/v1/messages",
        headers=headers,
        payload=corpo,
        stream_kind="anthropic",
    )
    uso_bruto = resposta_json.get("usage") or {}
    uso = normalizar_uso(uso_bruto)
    resultado = montar_resultado(
        provider="anthropic",
        model=model,
        input_text=input_text,
        instruction=instruction,
        output_text=extrair_texto_anthropic(resposta_json),
        request_id=extrair_request_id(resposta_json, resposta_http),
        usage=uso,
        extra=remover_nulos(
            {
                "server_tool_use": uso_bruto.get("server_tool_use"),
            }
        ),
    )
    custo = _calcular_custo(
        modelo=model,
        uso=uso,
        cache_ttl=None,
        inference_geo=None,
        modo_rapido=False,
        server_tool_use=uso_bruto.get("server_tool_use") or {},
    )
    _atualizar_custo_no_resultado(resultado, custo, origem="usage_x_pricing_page")
    return normalizar_resultado_publico(resultado)


def list_models(api_key=None, timeout=180):
    """Lista os modelos atualmente disponiveis na Anthropic."""
    chave = obter_chave_api("ANTHROPIC_API_KEY", api_key=api_key)
    resposta_json, _ = requisicao_json(
        metodo="GET",
        url="https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": chave,
            "anthropic-version": "2023-06-01",
        },
        timeout=timeout,
    )
    return resposta_json.get("data") or []


def _montar_mensagens_anthropic(input_text):
    """Converte o texto principal no formato minimo exigido pela API."""
    return [{"role": "user", "content": input_text}]


def _montar_thinking(
    model,
    reasoning="low",
):
    """Monta o objeto `thinking` da Anthropic."""
    nivel = _normalizar_reasoning(reasoning)
    if not nivel or not _modelo_suporta_reasoning(model):
        return None

    return remover_nulos(
        {
            "type": "adaptive" if "claude-opus-4-7" in (model or "") else "enabled",
            "budget_tokens": _ORCAMENTOS_REASONING.get(nivel),
        }
    )


def _calcular_custo(
    modelo,
    uso,
    cache_ttl="5m",
    inference_geo=None,
    modo_rapido=False,
    server_tool_use=None,
):
    """Calcula o custo em USD com base na tabela oficial da Anthropic."""
    precos = _resolver_preco_modelo(modelo, cache_ttl=cache_ttl, modo_rapido=modo_rapido)
    if not precos:
        return 0.0

    custo = calcular_custo_tokens(uso, precos)
    if _aplica_residencia_us(modelo, inference_geo):
        custo *= 1.1

    server_tool_use = server_tool_use or {}
    web_search_requests = server_tool_use.get("web_search_requests", 0) or 0
    if web_search_requests:
        custo += web_search_requests * 0.01

    return custo


def _resolver_preco_modelo(modelo, cache_ttl="5m", modo_rapido=False):
    """Resolve a tabela de precos do modelo informado."""
    modelo_normalizado = (modelo or "").lower()

    if modo_rapido and "claude-opus-4-6" in modelo_normalizado:
        return {
            "input": 30.0,
            "output": 150.0,
            "cache_write": 60.0 if cache_ttl == "1h" else 37.5,
            "cache_read": 3.0,
        }

    for chave, precos in sorted(_PRECOS_MODELOS.items(), key=lambda item: -len(item[0])):
        if chave not in modelo_normalizado:
            continue
        return {
            "input": precos["input"],
            "output": precos["output"],
            "cache_write": (
                precos["cache_write_1h"]
                if (cache_ttl or "").lower() == "1h"
                else precos["cache_write_5m"]
            ),
            "cache_read": precos["cache_read"],
        }

    return None


def _aplica_residencia_us(modelo, inference_geo):
    """Retorna se o multiplicador de data residency deve ser aplicado."""
    if (inference_geo or "").lower() != "us":
        return False

    modelo_normalizado = (modelo or "").lower()
    familias = (
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-sonnet-4-5",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
    )
    return any(familia in modelo_normalizado for familia in familias)


def _normalizar_reasoning(reasoning):
    """Normaliza o nivel de reasoning simplificado do wrapper."""
    if reasoning is None:
        return None
    reasoning = str(reasoning).strip().lower()
    if not reasoning or reasoning == "none":
        return None
    if reasoning in _ORCAMENTOS_REASONING:
        return reasoning
    raise ValueError("`reasoning` must be one of: low, medium, high, none, or None.")


def _modelo_suporta_reasoning(modelo):
    """Retorna se o wrapper deve enviar `thinking` para o modelo informado."""
    modelo_normalizado = (modelo or "").lower()
    familias = (
        "claude-opus-4",
        "claude-sonnet-4",
        "claude-haiku-4-5",
    )
    return any(familia in modelo_normalizado for familia in familias)
