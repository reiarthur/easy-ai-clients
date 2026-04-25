"""Cliente de geracao texto->texto para a API da OpenRouter.

Ultima atualizacao: 2026-04-23
"""

import time

from requests import exceptions as requests_exceptions

from ..post_processing import (
    atualizar_custo_no_resultado as _atualizar_custo_no_resultado,
)
from ..post_processing import (
    calcular_custo_catalogo_por_token as _calcular_custo_catalogo_por_token,
)
from ..post_processing import (
    montar_resultado_chat_compativel as _montar_resultado_chat_compativel,
)
from ..pre_processing import (
    listar_modelos_compativeis as _listar_modelos_compativeis,
)
from ..pre_processing import (
    obter_chave_api as _obter_chave_api,
)
from ..pre_processing import (
    remover_nulos as _remover_nulos,
)
from ..pre_processing import (
    requisicao_json as _requisicao_json,
)
from ._shared import (
    OPENROUTER_PARAMETERS,
)
from ._shared import (
    build_chat_payload as _build_chat_payload,
)
from ._shared import (
    execute_chat_request as _execute_chat_request,
)
from ._shared import (
    validate_kwargs as _validate_kwargs,
)

_CACHE_MODELOS = None


def generate(
    input_text,
    instruction=None,
    model="openai/gpt-oss-20b:free",
    **kwargs,
):
    """Generate text with OpenRouter. Full details: text/docs/openrouter.md."""
    _validate_kwargs(
        provider="openrouter",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=OPENROUTER_PARAMETERS,
    )
    corpo = _build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    if "usage" not in corpo:
        corpo["usage"] = {"include": True}
    resposta_json, resposta_http = _execute_chat_request(
        env_var="OPENROUTER_API_KEY",
        url="https://openrouter.ai/api/v1/chat/completions",
        payload=corpo,
    )
    return _montar_resultado_chat_compativel(
        provider="openrouter",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista o catalogo live da OpenRouter."""
    return _listar_modelos_compativeis(
        env_var="OPENROUTER_API_KEY",
        url_modelos="https://openrouter.ai/api/v1/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def update_cost(resultado):
    """Atualiza `cost_usd` consultando `/generation` e fallback por catalogo."""
    try:
        dados_generation = _consultar_generation(
            resultado.get("request_id"),
            model=resultado.get("model"),
        )
        if dados_generation:
            _aplicar_dados_generation(resultado, dados_generation)
            _atualizar_custo_no_resultado(
                resultado,
                dados_generation["_resolved_total_cost"],
                origem="generation_endpoint",
            )
            return resultado

        uso = resultado.get("usage") or {}
        provider_cost = uso.get("provider_cost")
        if provider_cost is not None:
            custo_imediato = float(provider_cost)
            if custo_imediato > 0 or _modelo_tem_preco_zero(resultado.get("model")):
                _atualizar_custo_no_resultado(
                    resultado,
                    custo_imediato,
                    origem="usage_immediate",
                )
                return resultado

        custo = _calcular_custo_catalogo(
            resultado.get("model"),
            uso,
        )
        if custo:
            _atualizar_custo_no_resultado(
                resultado,
                custo,
                origem="usage_x_models_endpoint",
            )
            return resultado

        _atualizar_custo_no_resultado(
            resultado,
            resultado.get("cost_usd") or 0.0,
            origem=resultado.get("cost_source") or "cost_lookup_failed",
        )
    except (RuntimeError, requests_exceptions.RequestException):
        _atualizar_custo_no_resultado(
            resultado,
            resultado.get("cost_usd") or 0.0,
            origem="cost_lookup_failed",
        )
    return resultado


def _resolver_custo(resultado, resposta_json=None, resposta_http=None):
    """Resolve custo via `usage.cost`, `/generation` ou catalogo live."""
    del resposta_json, resposta_http
    uso = resultado.get("usage") or {}
    provider_cost = uso.get("provider_cost")
    if provider_cost is not None:
        custo_imediato = float(provider_cost)
        if custo_imediato > 0 or _modelo_tem_preco_zero(resultado.get("model")):
            return custo_imediato, "usage_immediate"

    dados_generation = _consultar_generation(
        resultado.get("request_id"),
        model=resultado.get("model"),
    )
    if dados_generation:
        _aplicar_dados_generation(resultado, dados_generation)
        return dados_generation["_resolved_total_cost"], "generation_endpoint"

    custo = _calcular_custo_catalogo(resultado.get("model"), uso)
    return custo, "usage_x_models_endpoint"


def _calcular_custo_catalogo(modelo, uso):
    """Calcula custo usando o endpoint de modelos da OpenRouter."""
    item = _obter_modelo_catalogo(modelo)
    if not item:
        return 0.0

    return _calcular_custo_catalogo_por_token(uso, item.get("pricing") or {})


def _obter_modelo_catalogo(modelo):
    """Retorna o item do catalogo referente ao modelo solicitado."""
    return (_carregar_catalogo_modelos().get("por_id") or {}).get(modelo or "")


def _carregar_catalogo_modelos():
    """Carrega o catalogo da OpenRouter apenas uma vez por processo."""
    global _CACHE_MODELOS
    if _CACHE_MODELOS is None:
        _CACHE_MODELOS = _montar_cache_modelos(list_models())
    return _CACHE_MODELOS


def _montar_cache_modelos(modelos):
    """Organiza o catalogo em estruturas de lookup rapido por `id`."""
    return {
        "lista": modelos,
        "por_id": {item.get("id"): item for item in modelos if item.get("id")},
    }


def _transformar_modelos(resposta_json):
    """Normaliza a listagem retornada pelo endpoint `/models`."""
    return resposta_json.get("data") or []


def _consultar_generation(request_id, model=None):
    """Consulta `/generation` com polling curto ate o custo consolidar."""
    if not request_id:
        return None

    try:
        chave = _obter_chave_api("OPENROUTER_API_KEY")
    except RuntimeError:
        return None

    for tentativa in range(12):
        try:
            resposta_json, _ = _requisicao_json(
                metodo="GET",
                url="https://openrouter.ai/api/v1/generation",
                headers={"Authorization": f"Bearer {chave}"},
                params={"id": request_id},
            )
        except RuntimeError as erro:
            if tentativa < 11 and _erro_generation_ainda_nao_pronto(erro):
                time.sleep(1)
                continue
            return None

        dados = resposta_json.get("data") or {}
        total_cost = _resolver_total_cost_generation(dados, model=model)
        if total_cost is not None:
            dados["_resolved_total_cost"] = total_cost
            return dados

        if tentativa < 11:
            time.sleep(1)

    return None


def _resolver_total_cost_generation(dados, model=None):
    """Resolve `total_cost` do `/generation` distinguindo zero legitimo."""
    model = model or dados.get("model")
    total_cost = dados.get("total_cost")
    if total_cost is None:
        return None

    total_cost = float(total_cost)
    if total_cost == 0.0 and _modelo_tem_preco_positivo(model):
        return None
    return total_cost


def _aplicar_dados_generation(resultado, dados_generation):
    """Mescla tokens vindos do `/generation` no resultado final."""
    if dados_generation.get("model") and not resultado.get("model"):
        resultado["model"] = dados_generation.get("model")

    uso = dict(resultado.get("usage") or {})
    uso_generation = _remover_nulos(
        {
            "input_tokens": dados_generation.get("tokens_prompt"),
            "output_tokens": dados_generation.get("tokens_completion"),
            "total_tokens": (
                (dados_generation.get("tokens_prompt") or 0)
                + (dados_generation.get("tokens_completion") or 0)
            )
            or None,
            "reasoning_tokens": dados_generation.get("native_tokens_reasoning"),
            "provider_cost": dados_generation.get("_resolved_total_cost"),
        }
    )
    if uso_generation:
        uso.update(uso_generation)
        resultado["usage"] = uso


def _modelo_tem_preco_zero(modelo):
    """Retorna se o catalogo indica preco zero para o modelo informado."""
    pricing = ((_obter_modelo_catalogo(modelo) or {}).get("pricing") or {})
    return not _modelo_tem_preco_positivo(modelo) and bool(pricing)


def _modelo_tem_preco_positivo(modelo):
    """Retorna se o catalogo indica algum preco positivo no modelo."""
    pricing = ((_obter_modelo_catalogo(modelo) or {}).get("pricing") or {})
    return any(float(valor or 0) > 0 for valor in pricing.values())


def _erro_generation_ainda_nao_pronto(erro):
    """Retorna se o erro indica indexacao ainda nao concluida no endpoint."""
    mensagem = str(erro).lower()
    return "generation" in mensagem and "not found" in mensagem and "404" in mensagem
