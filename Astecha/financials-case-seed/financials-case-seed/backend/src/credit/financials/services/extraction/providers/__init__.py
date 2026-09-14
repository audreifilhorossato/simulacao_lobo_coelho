"""Registro de providers.

Este é o único lugar que sabe que provider existe. O resto do app pede
``get_provider()`` e recebe algo que satisfaz ``ExtractionProvider``.

Para plugar o seu:

    from credit.financials.services.extraction.providers.rule_based import (
        RuleBasedProvider,
    )

    _REGISTRY = {
        "naive": NaiveProvider,
        "rule_based": RuleBasedProvider,   # <- Sprint 1
        "llm": LLMProvider,                # <- Sprint 3
    }

Importe o SDK do LLM DENTRO do módulo do provider, nunca aqui: um import de
topo faz o app inteiro deixar de subir quando a biblioteca não está instalada.
"""

from __future__ import annotations

from credit.financials.services.extraction.providers.base import ExtractionProvider
from credit.financials.services.extraction.providers.naive import NaiveProvider
from django.conf import settings

_REGISTRY = {
    "naive": NaiveProvider,
}


def available() -> list[str]:
    return sorted(_REGISTRY)


def get_provider(name: str | None = None) -> ExtractionProvider:
    """Instancia o provider pedido, ou o de ``settings.FINANCIALS_EXTRACTION_PROVIDER``.

    Levanta ``ValueError`` com a lista do que existe — um nome errado no ``.env``
    tem que falhar alto e dizer o que era esperado, não cair num default
    silencioso que faz a métrica mentir.
    """
    key = (name or settings.FINANCIALS_EXTRACTION_PROVIDER or "").strip()
    if key not in _REGISTRY:
        raise ValueError(
            f"Provider de extracao '{key}' nao existe. Disponiveis: "
            f"{', '.join(available())}."
        )
    return _REGISTRY[key]()
