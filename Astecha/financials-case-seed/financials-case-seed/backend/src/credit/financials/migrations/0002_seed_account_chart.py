"""Semeia o plano de contas padronizado brasileiro.

PORTADO da plataforma Astecha (migration 0004 de lá).

Por que esta migration é estrutural, e não "dado de exemplo":
``FinancialStatementLine.account`` é uma FK com ``PROTECT`` para esta tabela, e
a tabela nasce VAZIA na 0001 — ou seja, até isto rodar, NENHUM balanço ou DRE
pode ser escrito, por superfície nenhuma. Não a remova, não a torne opcional.

Inserida nível a nível, para que o pai de uma linha sempre exista antes dela (a
FK é auto-referente). Idempotente: pula qualquer ``account_code`` que já exista.

Reverse é um no-op declarado: apagar o padrão bateria no PROTECT de qualquer
linha de demonstração já apontando para ele, e uma taxonomia não é algo que um
rollback deva levar embora em silêncio.
"""

from django.db import migrations


def seed(apps, schema_editor):
    AccountChart = apps.get_model("financials", "AccountChart")

    # Importado aqui, e nao no topo do modulo: migrations sao carregadas no
    # `migrate` de TODOS os apps, e um import de topo faria deste arquivo uma
    # dependencia de boot do pacote de services.
    from credit.financials.services.account_chart_service import derive
    from credit.financials.services.chart_defaults import STANDARD_CHART

    existing = set(AccountChart.objects.values_list("account_code", flat=True))

    rows = []
    for order, (code, name) in enumerate(STANDARD_CHART):
        derived = derive(code)
        rows.append(
            {
                "account_code": code,
                "account_name": name,
                "account_type": derived["account_type"],
                "statement": derived["statement"],
                "parent_id": derived["parent_code"],
                "level": derived["level"],
                "display_order": order * 10,
                "origin": "STANDARD",
            }
        )

    # Nivel a nivel: garante o pai antes do filho.
    for level in sorted({r["level"] for r in rows}):
        AccountChart.objects.bulk_create(
            [
                AccountChart(**r)
                for r in rows
                if r["level"] == level and r["account_code"] not in existing
            ]
        )


def unseed(apps, schema_editor):
    """No-op deliberado — ver o docstring do modulo."""


class Migration(migrations.Migration):
    dependencies = [("financials", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
