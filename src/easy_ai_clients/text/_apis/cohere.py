"""Cliente de geracao texto->texto para a Chat API v2 da Cohere.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import (
    atualizar_custo_no_resultado as _atualizar_custo_no_resultado,
)
from ..post_processing import (
    calcular_custo_tokens,
    extrair_request_id,
    extrair_texto_cohere,
    montar_resultado,
    normalizar_resultado_publico,
    normalizar_uso,
)
from ..pre_processing import (
    obter_chave_api,
    remover_nulos,
    requisicao_json,
)
from ._shared import COHERE_CHAT_PARAMETERS, execute_json_request, validate_kwargs

_PRECOS_MODELOS = {
    "command-r7b-12-2024": {"billed_input": 0.0375, "billed_output": 0.15},
    "command-r-08-2024": {"billed_input": 0.15, "billed_output": 0.60},
    "command-r-plus-08-2024": {"billed_input": 2.5, "billed_output": 10.0},
    "command-a-03-2025": {"billed_input": 2.5, "billed_output": 10.0},
    "command-a-reasoning-08-2025": {"billed_input": 0.0, "billed_output": 0.0},
    "c4ai-aya-expanse-32b": {"billed_input": 0.5, "billed_output": 1.5},
}


def generate(
    input_text,
    instruction=None,
    model="command-r7b-12-2024",
    **kwargs,
):
    """Generate text with Cohere Chat v2. Full details: text/docs/cohere.md."""
    validate_kwargs(
        provider="cohere",
        api="v2/chat",
        model=model,
        kwargs=kwargs,
        supported_parameters=COHERE_CHAT_PARAMETERS,
    )
    chave = obter_chave_api("COHERE_API_KEY")
    parametros = dict(kwargs)
    corpo = remover_nulos(
        {
            "model": model,
            "messages": parametros.pop(
                "messages",
                _montar_mensagens_cohere(
                    input_text=input_text,
                    instruction=instruction,
                ),
            ),
        }
    )
    corpo.update(remover_nulos(parametros))

    resposta_json, resposta_http = execute_json_request(
        method="POST",
        url="https://api.cohere.com/v2/chat",
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
        },
        payload=corpo,
        stream_kind="cohere",
    )
    uso = normalizar_uso(resposta_json.get("usage") or {})
    resultado = montar_resultado(
        provider="cohere",
        model=model,
        input_text=input_text,
        instruction=instruction,
        output_text=extrair_texto_cohere(resposta_json),
        request_id=extrair_request_id(resposta_json, resposta_http),
        usage=uso,
    )
    custo = _calcular_custo(modelo=model, uso=uso)
    _atualizar_custo_no_resultado(resultado, custo, origem="billed_units_x_pricing_page")
    return normalizar_resultado_publico(resultado)


def list_models(api_key=None, timeout=180):
    """Lista os modelos da Cohere que expõem endpoint de chat."""
    chave = obter_chave_api("COHERE_API_KEY", api_key=api_key)
    resposta_json, _ = requisicao_json(
        metodo="GET",
        url="https://api.cohere.com/v1/models",
        headers={"Authorization": f"Bearer {chave}"},
        timeout=timeout,
    )
    modelos = resposta_json.get("models") or []
    return [item for item in modelos if "chat" in (item.get("endpoints") or [])]


def _montar_mensagens_cohere(input_text, instruction=None):
    """Converte a chamada minima para a estrutura de mensagens da Cohere."""
    mensagens = []
    if instruction:
        mensagens.append({"role": "system", "content": instruction})

    mensagens.append({"role": "user", "content": input_text})
    return mensagens


def _calcular_custo(modelo, uso):
    """Calcula o custo monetario da chamada da Cohere."""
    precos = _resolver_preco_modelo(modelo)
    if not precos:
        return 0.0
    return calcular_custo_tokens(uso, precos)


def _resolver_preco_modelo(modelo):
    """Resolve a tabela de precos do modelo informado."""
    modelo_normalizado = (modelo or "").lower()
    for chave, precos in sorted(_PRECOS_MODELOS.items(), key=lambda item: -len(item[0])):
        if chave in modelo_normalizado:
            return precos
    return None
