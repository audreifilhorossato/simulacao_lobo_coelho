"""A COSTURA DE MIGRAÇÃO Nº 2 — a interface do provider de extração.

Regra R8, e é dura: **nenhum ``import anthropic`` / ``openai`` /
``google.generativeai`` / ``ollama`` pode existir fora do pacote
``providers/``.** O resto da aplicação conhece apenas ``ExtractionProvider``.

Por quê: na Astecha o provider vira Snowflake Cortex ou a API da Anthropic
rodando dentro da conta do cliente. Se o SDK do seu provedor estiver espalhado
pela camada de service, a migração deixa de ser "trocar um arquivo" e vira
reescrever o app.

Como acrescentar o seu provider:

1. Crie ``providers/<nome>.py`` com uma classe que implemente ``extract``.
2. Registre em ``providers/__init__.py`` no dicionário ``_REGISTRY``.
3. Aponte ``FINANCIALS_EXTRACTION_PROVIDER=<nome>`` no ``.env``.

Nunca leia chave de API dentro do código: só ``os.environ``. Chave commitada é
critério de reprovação (regra R15).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from credit.financials.services.extraction.types import (
    ExtractionResult,
    ParsedDocument,
)


@runtime_checkable
class ExtractionProvider(Protocol):
    """Transforma um documento já parseado em rascunhos de demonstração.

    Contrato (o teste ``tests/test_provider_contract.py`` cobra todos):

    - ``name`` identifica o provider nas métricas. Estável entre execuções.
    - ``extract`` NUNCA levanta exceção por documento ruim: um documento que
      não deu para ler devolve ``ExtractionResult`` com ``drafts=[]`` e o
      motivo em ``warnings``. Só condição realmente excepcional (a rede caiu)
      propaga.
    - ``extract`` é PURA em relação ao banco: não escreve nada, não lê nada do
      ORM. Quem persiste é o service que chama.
    - O mesmo documento tem que produzir o mesmo resultado dentro do razoável.
      Com LLM, fixe ``temperature=0`` — sem isso a métrica de acurácia vira
      ruído e você não consegue provar melhora nenhuma.
    """

    name: str

    def extract(self, document: ParsedDocument) -> ExtractionResult: ...
