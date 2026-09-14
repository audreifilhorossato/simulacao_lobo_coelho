"""Derivação e escrita do plano de contas.

PORTADO VERBATIM da plataforma Astecha.

``level`` e ``parent`` NUNCA vêm do chamador — são função apenas do
``account_code`` pontuado.

Regras de escrita impostas aqui (não só na view, para que nada as burle
chamando este módulo direto):

- ``account_type`` / ``statement`` / ``level`` / ``parent`` são sempre
  derivados do ``account_code``. O chamador não pode defini-los, mesmo
  incluindo-os no payload (são simplesmente ignorados). É isso que torna
  "uma DESPESA pendurada no ATIVO" irrepresentável, e não meramente
  desaconselhada.
- Criar um novo grupo de nível 1 é recusado — os seis grupos de
  ``chart_defaults.GROUPS`` são a taxonomia inteira.
- Linha semeada como ``ORIGIN='STANDARD'`` é imutável por este service:
  editar ou apagar levanta ``ConflictError``.
"""

from credit.financials.models.account_chart import AccountChart
from credit.financials.services.chart_defaults import GROUPS
from credit.financials.services.errors import ConflictError
from django.db.models import ProtectedError


def derive(account_code: str) -> dict:
    """``{"level", "parent_code", "account_type", "statement"}`` de um código.

    ``parent_code`` é ``None`` no nível 1. Levanta ``ValueError`` para código
    cujo grupo de nível 1 não é um dos padrão — é essa a checagem que impede
    inventar um sétimo grupo raiz e criar em silêncio uma taxonomia contra a
    qual ninguém consegue comparar.
    """
    code = str(account_code or "").strip()
    if not code:
        raise ValueError("account_code vazio.")

    parts = code.split(".")
    group = parts[0]
    if group not in GROUPS:
        raise ValueError(
            f"Grupo '{group}' não existe. Códigos começam por um de: "
            f"{', '.join(sorted(GROUPS))}."
        )

    account_type, statement = GROUPS[group]
    return {
        "level": len(parts),
        "parent_code": ".".join(parts[:-1]) if len(parts) > 1 else None,
        "account_type": account_type,
        "statement": statement,
    }


def serialize(account: AccountChart) -> dict:
    return {
        "account_code": account.account_code,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "statement": account.statement,
        "parent": account.parent_id,
        "level": account.level,
        "display_order": account.display_order,
        "origin": account.origin,
    }


def _field(entry: dict, *names):
    """Aceita chave em MAIÚSCULA ou minúscula — um payload montado copiando uma
    linha lida de volta (que vem em MAIÚSCULA) tem que funcionar igual a um
    escrito à mão em minúscula."""
    for name in names:
        if name in entry and entry[name] not in (None, ""):
            return entry[name]
    return None


def _next_display_order(parent_code):
    """Uma linha CUSTOM nova ordena depois dos irmãos existentes, ou logo após
    o pai se for o primeiro filho. Não é sem lacunas de propósito — empate
    desempata por ``account_code``, o que basta para uma árvore estável."""
    if parent_code is None:
        return 0
    siblings_max = (
        AccountChart.objects.filter(parent_id=parent_code)
        .order_by("-display_order")
        .values_list("display_order", flat=True)
        .first()
    )
    if siblings_max is not None:
        return siblings_max + 1
    parent = AccountChart.objects.filter(account_code=parent_code).first()
    return (parent.display_order if parent else 0) + 1


def upsert_account(entry: dict) -> dict:
    """Cria ou atualiza UMA conta CUSTOM.

    ``entry`` precisa apenas de ``ACCOUNT_CODE``/``ACCOUNT_NAME`` (ou
    minúsculas) — o resto é derivado do código, e as chaves derivadas presentes
    em ``entry`` são silenciosamente ignoradas, não rejeitadas.
    """
    code = str(_field(entry, "ACCOUNT_CODE", "account_code") or "").strip()
    name = str(_field(entry, "ACCOUNT_NAME", "account_name") or "").strip()
    if not code:
        raise ValueError("ACCOUNT_CODE é obrigatório.")
    if not name:
        raise ValueError(f"ACCOUNT_NAME é obrigatório (conta '{code}').")

    derived = derive(code)
    parent_code = derived["parent_code"]
    if (
        parent_code is not None
        and not AccountChart.objects.filter(account_code=parent_code).exists()
    ):
        raise ValueError(
            f"Conta pai '{parent_code}' não existe — crie-a antes de '{code}'."
        )

    existing = AccountChart.objects.filter(account_code=code).first()
    if existing is not None and existing.origin == AccountChart.ORIGIN_STANDARD:
        raise ConflictError(
            f"'{code}' é uma conta padrão (ORIGIN=STANDARD) e não pode ser "
            "alterada — crie uma conta CUSTOM sob ela em vez disso."
        )

    account, _created = AccountChart.objects.update_or_create(
        account_code=code,
        defaults={
            "account_name": name,
            "account_type": derived["account_type"],
            "statement": derived["statement"],
            "parent_id": parent_code,
            "level": derived["level"],
            "display_order": (
                existing.display_order
                if existing is not None
                else _next_display_order(parent_code)
            ),
            "origin": AccountChart.ORIGIN_CUSTOM,
        },
    )
    return serialize(account)


def upsert_many(entries: list) -> dict:
    """Upsert por linha, com coleta de erro por linha — ao contrário da escrita
    em lote de demonstrações, contas não têm invariante de conjunto a proteger,
    então uma linha ruim é pulada em vez de afundar o lote inteiro."""
    inserted = 0
    updated = 0
    errors = []
    for i, entry in enumerate(entries, start=1):
        code = str(_field(entry, "ACCOUNT_CODE", "account_code") or "").strip()
        try:
            existed = code and AccountChart.objects.filter(account_code=code).exists()
            upsert_account(entry)
            if existed:
                updated += 1
            else:
                inserted += 1
        except (ValueError, ConflictError) as exc:
            errors.append({"row": i, "account_code": code, "message": str(exc)})
    return {
        "inserted": inserted,
        "updated": updated,
        "total": len(entries),
        "errors": errors,
    }


def delete_account(code: str) -> None:
    account = AccountChart.objects.filter(account_code=code).first()
    if account is None:
        raise LookupError(f"Conta '{code}' não existe.")
    if account.origin == AccountChart.ORIGIN_STANDARD:
        raise ConflictError(
            f"'{code}' é uma conta padrão (ORIGIN=STANDARD) e não pode ser excluída."
        )
    try:
        account.delete()
    except ProtectedError:
        raise ConflictError(
            f"Não é possível excluir '{code}': existem linhas de demonstração "
            "financeira apontando para esta conta."
        ) from None
