"""Cliente de geracao texto->texto para a API da Mistral AI.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import calcular_custo_tokens, montar_resultado_chat_compativel
from ..pre_processing import (
    listar_modelos_compativeis,
)
from ._shared import (
    MISTRAL_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_PRECOS_MODELOS = {
    "mistral-large-2512": {"input": 0.5, "output": 1.5},
    "mistral-large-latest": {"input": 0.5, "output": 1.5},
    "mistral-medium-2508": {"input": 0.4, "output": 2.0},
    "mistral-medium-2505": {"input": 0.4, "output": 2.0},
    "mistral-medium-latest": {"input": 0.4, "output": 2.0},
    "mistral-medium": {"input": 0.4, "output": 2.0},
    "mistral-small-2603": {"input": 0.15, "output": 0.6},
    "mistral-small-2506": {"input": 0.1, "output": 0.3},
    "mistral-small-latest": {"input": 0.15, "output": 0.6},
    "mistral-small": {"input": 0.15, "output": 0.6},
    "magistral-medium-2509": {"input": 2.0, "output": 5.0},
    "magistral-medium-latest": {"input": 2.0, "output": 5.0},
    "magistral-small-2509": {"input": 0.5, "output": 1.5},
    "magistral-small-latest": {"input": 0.5, "output": 1.5},
    "codestral-2508": {"input": 0.3, "output": 0.9},
    "codestral-latest": {"input": 0.3, "output": 0.9},
    "devstral-medium-2507": {"input": 0.4, "output": 2.0},
    "devstral-medium-latest": {"input": 0.4, "output": 2.0},
    "ministral-14b-2512": {"input": 0.2, "output": 0.2},
    "voxtral-small-2507": {"input": 0.1, "output": 0.3},
}


def generate(
    input_text,
    instruction=None,
    model="mistral-small-2506",
    **kwargs,
):
    """Generate text with Mistral. Full details: text/docs/mistral.md."""
    validate_kwargs(
        provider="mistral",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=MISTRAL_PARAMETERS,
    )
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )

    resposta_json, resposta_http = execute_chat_request(
        env_var="MISTRAL_API_KEY",
        url="https://api.mistral.ai/v1/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="mistral",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista os modelos chat-capable atualmente expostos pela Mistral."""
    return listar_modelos_compativeis(
        env_var="MISTRAL_API_KEY",
        url_modelos="https://api.mistral.ai/v1/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo da chamada usando a tabela oficial da Mistral."""
    del resposta_json, resposta_http
    custo = _calcular_custo(resultado.get("model"), resultado.get("usage") or {})
    return custo, "usage_x_model_card"


def _calcular_custo(modelo, uso):
    """Calcula custo para modelos textuais conhecidos da Mistral."""
    precos = _resolver_preco_modelo(modelo)
    if not precos:
        return 0.0
    return calcular_custo_tokens(uso, precos)


def _resolver_preco_modelo(modelo):
    """Resolve aliases conhecidos da Mistral."""
    modelo_normalizado = (modelo or "").lower()
    for chave, precos in sorted(_PRECOS_MODELOS.items(), key=lambda item: -len(item[0])):
        if chave in modelo_normalizado:
            return precos
    return None


def _transformar_modelos(resposta_json):
    """Filtra apenas modelos com capacidade de chat/completions."""
    modelos = resposta_json.get("data") or []
    return [
        item
        for item in modelos
        if (item.get("capabilities") or {}).get("completion_chat")
    ]
