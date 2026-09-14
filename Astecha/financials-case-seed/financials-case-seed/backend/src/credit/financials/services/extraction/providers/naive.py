"""O provider de piso: não extrai nada.

Ele existe por um motivo só — provar que o arreio de avaliação (``eval/run.py``)
funciona de ponta a ponta ANTES de vocês escreverem uma linha de extração. Ele
roda, devolve zero rascunho e tira **0% de acurácia**.

Esse é o seu chão. Na Sprint 1 vocês entregam ``rule_based`` e o número tem que
sair do zero; na Sprint 3 entregam ``llm`` e o número tem que subir de novo.
Os três números lado a lado são a apresentação final.

**Não apague este arquivo.** Ele é o controle: se um dia a acurácia do
``rule_based`` empatar com a do ``naive``, o bug está no arreio, não no
provider.
"""

from __future__ import annotations

from credit.financials.services.extraction.types import (
    ExtractionResult,
    ParsedDocument,
)


class NaiveProvider:
    name = "naive"

    def extract(self, document: ParsedDocument) -> ExtractionResult:
        return ExtractionResult(
            drafts=[],
            provider=self.name,
            model="none",
            prompt_version="none",
            warnings=[
                "NaiveProvider nao extrai nada: e o piso de comparacao. "
                "Implemente rule_based e llm."
            ],
        )
