"""Pós-processamento compartilhado para provedores de `analyze`.

Última atualização: 2026-04-23
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .._common.provider_utils import analyze_result
from .._common.types import AnalyzeOperationResult


def build_analyze_result(
    *,
    request_id: str = "",
    cost_usd: Decimal | float = 0.0,
    cost_source: str | None = None,
    cost_is_estimated: bool = True,
    cost_details: dict[str, Any] | None = None,
    input_text: str = "",
    output: str = "",
) -> AnalyzeOperationResult:
    """Monta o resultado público normalizado de `analyze`.

    ### Parâmetros:
        request_id: Identificador exposto pelo provedor.
        cost_usd: Custo final conhecido da requisição em USD.
        cost_source: Origem do custo quando conhecida.
        cost_is_estimated: Indica se o custo foi estimado.
        cost_details: Metadados públicos do custo.
        input_text: Prompt normalizado enviado ao provedor.
        output: Texto retornado pelo provedor ou mensagem de erro/bloqueio.

    ### Retorna:
        Dict público normalizado de `analyze`.
    """

    return analyze_result(
        request_id=request_id,
        cost_usd=cost_usd,
        cost_source=cost_source,
        cost_is_estimated=cost_is_estimated,
        cost_details=cost_details,
        input_text=input_text,
        output=output,
    )
