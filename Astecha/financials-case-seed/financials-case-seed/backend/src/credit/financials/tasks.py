"""Tasks Celery do app.

Regra R7: **este é o único lugar onde trabalho assíncrono pode nascer.** Nada de
``threading``, ``concurrent.futures``, ``BackgroundTasks`` ou
``asyncio.create_task`` — a aplicação roda em vários processos e um job que vive
na memória de um deles não existe para os outros.

Duas regras que os alunos costumam quebrar e que valem nota:

1. **A lógica NÃO mora na task.** A task orquestra: pega o documento, chama o
   service, grava o status. Se você escrever o parser dentro da task, ele fica
   intestável sem Celery.
2. **Task não se reagenda.** Nada de ``apply_async(countdown=...)`` no fim de
   uma task, nem ``self.retry()`` como agendador. Isso cria laço de tarefas que
   duplica a cada restart.
"""

import logging

from celery import shared_task
from credit.financials.models import SourceDocument

logger = logging.getLogger(__name__)


@shared_task(name="credit.financials.parse_document")
def parse_document(document_id: int) -> dict:
    """Esqueleto: marca PARSING, chamaria o parser, marca PARSED ou FAILED.

    O que falta (Sprint 1): substituir o corpo por uma chamada ao seu
    ``services/parsing.py``, que devolve um ``ParsedDocument``.

    Repare no ``try/except`` com ``FAILED``: um documento que quebra o parser
    NÃO pode deixar o registro preso em ``PARSING`` para sempre. Um status que
    nunca sai de "processando" é a reclamação nº 1 de quem opera este tipo de
    tela.
    """
    document = SourceDocument.objects.filter(pk=document_id).first()
    if document is None:
        logger.warning("parse_document: documento %s nao existe", document_id)
        return {"document_id": document_id, "status": "NOT_FOUND"}

    document.processing_status = SourceDocument.STATUS_PARSING
    document.save(update_fields=["processing_status"])

    try:
        # TODO Sprint 1:
        #   parsed = parsing.parse(document)
        #   document.parsed_text = parsed.text
        raise NotImplementedError(
            "Implemente services/parsing.py (PDF nativo, OCR e XLSX)."
        )
    except Exception as exc:
        logger.exception("parse_document falhou para %s", document_id)
        document.processing_status = SourceDocument.STATUS_FAILED
        document.save(update_fields=["processing_status"])
        return {"document_id": document_id, "status": "FAILED", "error": str(exc)}


# TODO (Sprint 1/3):
# @shared_task(name="credit.financials.extract_document")
# def extract_document(document_id: int, provider_name: str | None = None) -> dict:
#     """Roda o provider e grava EXTRACTION + EXTRACTION_LINE.
#
#     Grave o nome do provider, o modelo e a versao do prompt na EXTRACTION.
#     Sem isso voce nao consegue responder "a acuracia caiu depois de qual
#     mudanca?" — e essa pergunta vai aparecer.
#     """
