"""Escrita em lote de demonstrações + linhas — o caminho de escrita central.

PORTADO VERBATIM da plataforma Astecha (a única diferença é o alias de banco).
**Este é o alvo do seu pipeline.** Quando o analista aprova um rascunho de
extração, o seu código monta o payload deste service e chama
``write_statements``. Não escreva um segundo caminho de escrita.

Duas fases por construção, e as duas entradas públicas compartilham a fase um:

1. ``_validate_batch`` — SÓ LEITURA. Confere existência e consistência contra o
   banco (empresa, contas, documento de origem, demonstração já existente a
   substituir). Nada é escrito aqui, então não custa nada rodar duas vezes:
   ``validate_statements`` (o diagnóstico) e ``write_statements`` (a escrita)
   chamam exatamente a mesma função — não existe uma segunda cópia das regras
   para divergir.
2. ``_write_batch`` — só é alcançada quando a fase um não achou erro duro.
   Tranca a chave natural de cada demonstração do payload e escreve tudo dentro
   de UMA transação: se qualquer coisa falhar no meio, o lote inteiro volta
   atrás. O conjunto de linhas de uma demonstração é sempre substituição total
   (apaga e insere), nunca merge — um merge não consegue expressar "esta linha
   foi removida", então um reenvio corrigido deixaria uma linha fantasma e
   contaria em dobro em silêncio.

Chave de idempotência: ``(company, statement_type, period_end_date)`` — o
próprio ``unique_together`` do model. Reenviar o payload idêntico converge
(mesmo STATEMENT_ID, mesmas linhas); reenviar depois de um timeout de rede é
sempre seguro, porque a escrita é tudo-ou-nada sobre essa mesma chave.
"""

import calendar

from credit.financials.models import (
    AccountChart,
    Company,
    FinancialStatement,
    FinancialStatementLine,
    SourceDocument,
)
from credit.financials.services import checks_service
from credit.financials.services.errors import ConflictError
from django.conf import settings
from django.core.cache import caches
from django.db import transaction

#: Envolve UMA requisição síncrona; longo o bastante para cobrir uma transação
#: lenta de várias demonstrações, curto o bastante para se curar rápido se um
#: worker morrer no meio da requisição.
_LOCK_TTL = 30


def _cache():
    """Cache COMPARTILHADO (Redis) — o Snowflake não impõe nem a FK de
    FinancialStatementLine.account nem o unique_together deste model, então dois
    POSTs concorrentes para a mesma chave natural realmente correm um contra o
    outro; o lock precisa valer ENTRE processos, o que o LocMem 'default' não
    consegue fazer. Ver regra R6."""
    return caches["shared"]


def _lock_key(company_id, statement_type, period_end_date) -> str:
    return (
        f"financials:stmt:{company_id}:{statement_type}:{period_end_date.isoformat()}"
    )


def _is_month_end(d) -> bool:
    return d.day == calendar.monthrange(d.year, d.month)[1]


def _validate_batch(company_id, statements_data):
    """Devolve ``(errors, prepared, company)``.

    ``errors``: ``[{"statement_index", "line_index"?, "account_code"?, "message"}]``
    — ``statement_index`` é ``None`` para erro do payload como um todo.
    ``prepared[i]`` carrega tudo o que ``_write_batch`` precisa para a
    demonstração ``i`` — instâncias já resolvidas, não dicts crus.
    """
    errors = []
    prepared = []

    try:
        company = Company.objects.get(pk=company_id)
    except Company.DoesNotExist:
        errors.append(
            {"statement_index": None, "message": f"Company {company_id} não existe."}
        )
        return errors, prepared, None

    for s_idx, stmt in enumerate(statements_data):
        stmt_errors = []
        statement_type = stmt["statement_type"]
        period_end_date = stmt["period_end_date"]
        lines = stmt["lines"]

        if not _is_month_end(period_end_date):
            stmt_errors.append(
                {
                    "statement_index": s_idx,
                    "message": (
                        f"PERIOD_END_DATE {period_end_date} não é o último dia do mês."
                    ),
                }
            )

        source_document = None
        source_document_id = stmt.get("source_document_id")
        if source_document_id:
            try:
                source_document = SourceDocument.objects.get(pk=source_document_id)
                if source_document.company_id != company.id:
                    stmt_errors.append(
                        {
                            "statement_index": s_idx,
                            "message": (
                                f"SOURCE_DOCUMENT_ID {source_document_id} "
                                "pertence a outra empresa."
                            ),
                        }
                    )
            except SourceDocument.DoesNotExist:
                stmt_errors.append(
                    {
                        "statement_index": s_idx,
                        "message": (
                            f"SOURCE_DOCUMENT_ID {source_document_id} não existe."
                        ),
                    }
                )

        clean_lines, line_errors = _validate_lines(s_idx, statement_type, lines)
        stmt_errors.extend(line_errors)

        existing = FinancialStatement.objects.filter(
            company=company,
            statement_type=statement_type,
            period_end_date=period_end_date,
        ).first()
        overwrite = bool(stmt.get("overwrite"))
        if (
            existing is not None
            and existing.status == FinancialStatement.STATUS_FINAL
            and not overwrite
        ):
            stmt_errors.append(
                {
                    "statement_index": s_idx,
                    "message": (
                        f"{statement_type} de {period_end_date} já existe como "
                        "FINAL — passe OVERWRITE=true para substituir."
                    ),
                }
            )

        errors.extend(stmt_errors)
        prepared.append(
            {
                "statement_type": statement_type,
                "period_end_date": period_end_date,
                "period_type": stmt["period_type"],
                "currency": stmt.get("currency") or "BRL",
                "source_document": source_document,
                "existing": existing,
                "lines": clean_lines,
            }
        )

    return errors, prepared, company


def _validate_lines(s_idx, statement_type, lines):
    """Conferências semânticas por linha contra o plano. Duplicata sinaliza
    TODA ocorrência do código repetido, não só a segunda: não há como saber
    qual das duas idênticas é a "certa", então nenhuma é confiável o bastante
    para escrever."""
    codes = [line["account_code"] for line in lines]
    code_counts = {}
    for code in codes:
        code_counts[code] = code_counts.get(code, 0) + 1

    chart_rows = {
        a.account_code: a for a in AccountChart.objects.filter(account_code__in=codes)
    }

    clean_lines = []
    errors = []
    for l_idx, line in enumerate(lines):
        code = line["account_code"]

        if code_counts[code] > 1:
            errors.append(
                {
                    "statement_index": s_idx,
                    "line_index": l_idx,
                    "account_code": code,
                    "message": (
                        f"'{code}' aparece {code_counts[code]}x nesta "
                        "demonstração — cada conta só pode aparecer uma vez."
                    ),
                }
            )
            continue

        account = chart_rows.get(code)
        if account is None:
            errors.append(
                {
                    "statement_index": s_idx,
                    "line_index": l_idx,
                    "account_code": code,
                    "message": f"ACCOUNT_CODE '{code}' não existe no plano de contas.",
                }
            )
            continue

        if account.statement != statement_type:
            errors.append(
                {
                    "statement_index": s_idx,
                    "line_index": l_idx,
                    "account_code": code,
                    "message": (
                        f"'{code}' pertence a {account.statement}, não a "
                        f"{statement_type}."
                    ),
                }
            )
            continue

        clean_lines.append(
            {
                "account": account,
                "raw_label": line["raw_label"],
                "value": line["value"],
                "notes": line.get("notes"),
            }
        )

    return clean_lines, errors


def _format_errors(errors: list) -> str:
    parts = []
    for e in errors:
        loc = (
            f"demonstração #{e['statement_index']}"
            if e.get("statement_index") is not None
            else "payload"
        )
        if e.get("line_index") is not None:
            loc += f", linha {e['line_index']}"
        parts.append(f"{loc}: {e['message']}")
    return f"{len(errors)} erro(s): " + " | ".join(parts)


def validate_statements(payload: dict) -> dict:
    """Roda exatamente a validação que ``write_statements`` rodaria, sem nunca
    escrever. Um payload ruim é reportado como DADO, não como erro que o
    chamador tenha que tratar de forma especial."""
    company_id = payload["company_id"]
    errors, prepared, _company = _validate_batch(company_id, payload["statements"])
    would = [
        {
            "statement_type": p["statement_type"],
            "period_end_date": str(p["period_end_date"]),
            "line_count": len(p["lines"]),
            "would": "replace" if p["existing"] is not None else "create",
        }
        for p in prepared
    ]
    return {
        "verdict": "ready" if not errors else "action_required",
        "would": would,
        "errors": errors,
    }


def write_statements(payload: dict, *, execution_user: str) -> dict:
    """Valida e, só se o lote inteiro estiver limpo, escreve tudo numa
    transação. Levanta ``ValueError`` (-> 400, nada escrito) se qualquer
    validação dura falhar em qualquer lugar do payload, e ``ConflictError``
    (-> 409, nada escrito) se uma chave natural já estiver sendo escrita por
    outra requisição."""
    company_id = payload["company_id"]
    errors, prepared, company = _validate_batch(company_id, payload["statements"])
    if errors:
        raise ValueError(_format_errors(errors))

    return {"results": _write_batch(company, prepared, execution_user=execution_user)}


def _write_batch(company, prepared: list, *, execution_user: str) -> list:
    lock_keys = []
    try:
        for p in prepared:
            key = _lock_key(company.id, p["statement_type"], p["period_end_date"])
            if not _cache().add(key, "1", _LOCK_TTL):
                raise ConflictError(
                    f"{p['statement_type']} de {p['period_end_date']} está sendo "
                    "escrita por outra requisição agora — tente novamente em "
                    "alguns segundos."
                )
            lock_keys.append(key)

        results = []
        with transaction.atomic(using=settings.FINANCIALS_DB_ALIAS):
            for p in prepared:
                statement, created = FinancialStatement.objects.update_or_create(
                    company=company,
                    statement_type=p["statement_type"],
                    period_end_date=p["period_end_date"],
                    defaults={
                        "period_type": p["period_type"],
                        "currency": p["currency"],
                        "source_document": p["source_document"],
                        "status": FinancialStatement.STATUS_DRAFT,
                        "extracted_by": execution_user,
                    },
                )
                FinancialStatementLine.objects.filter(statement=statement).delete()
                FinancialStatementLine.objects.bulk_create(
                    [
                        FinancialStatementLine(
                            statement=statement,
                            account=line["account"],
                            raw_label=line["raw_label"],
                            value=line["value"],
                            notes=line.get("notes"),
                        )
                        for line in p["lines"]
                    ]
                )

                checks = checks_service.run_checks(p["statement_type"], p["lines"])
                if (
                    p["existing"] is not None
                    and p["existing"].status == FinancialStatement.STATUS_FINAL
                ):
                    checks.append(
                        {
                            "check": "OVERWROTE_FINAL",
                            "status": "INFO",
                            "severity": "INFO",
                            "message": (
                                "Uma demonstração FINAL existente foi "
                                "substituída (OVERWRITE=true)."
                            ),
                        }
                    )

                results.append(
                    {
                        "statement_id": statement.id,
                        "statement_type": p["statement_type"],
                        "period_end_date": str(p["period_end_date"]),
                        "created": created,
                        "line_count": len(p["lines"]),
                        "checks": checks,
                    }
                )
        return results
    finally:
        for key in lock_keys:
            _cache().delete(key)


def delete_statement(statement_id) -> dict:
    """Só DRAFT — uma demonstração FINAL foi, por construção, escrita com
    OVERWRITE confirmado explicitamente ao menos uma vez; apagá-la de vez (em
    vez de substituí-la pelo caminho normal) não tem essa confirmação."""
    statement = FinancialStatement.objects.filter(pk=statement_id).first()
    if statement is None:
        raise LookupError(f"Demonstração {statement_id} não existe.")
    if statement.status == FinancialStatement.STATUS_FINAL:
        raise ConflictError(
            f"Demonstração {statement_id} é FINAL — não pode ser excluída "
            "diretamente. Reposte com OVERWRITE=true para substituí-la."
        )
    statement.delete()
    return {"statement_id": statement_id, "deleted": True}
