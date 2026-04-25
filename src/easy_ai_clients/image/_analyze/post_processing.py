"""Pós-processamento compartilhado para provedores de `analyze`.

Última atualização: 2026-04-23
"""

from __future__ import annotations

from decimal import Decimal

from .._common.provider_utils import analyze_result
from .._common.types import AnalyzeOperationResult


def build_analyze_result(
    *,
    request_id: str = "",
    cost_usd: Decimal | float = 0.0,
    input_text: str = "",
    output: str = "",
) -> AnalyzeOperationResult:
    """Monta o resultado público normalizado de `analyze`.

    ### Parâmetros:
        request_id: Identificador exposto pelo provedor.
        cost_usd: Custo final conhecido da requisição em USD.
        input_text: Prompt normalizado enviado ao provedor.
        output: Texto retornado pelo provedor ou mensagem de erro/bloqueio.

    ### Retorna:
        Dict com exatamente as chaves `request_id`, `cost_usd`,
        `input_text` e `output`, nessa ordem.
    """

    return analyze_result(
        request_id=request_id,
        cost_usd=cost_usd,
        input_text=input_text,
        output=output,
    )
