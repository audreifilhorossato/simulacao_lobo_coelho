"""Conferências contábeis de UMA demonstração — funções puras, sem ORM.

PORTADO VERBATIM da plataforma Astecha. NÃO ALTERE AS REGRAS — elas são o
contrato de qualidade contra o qual o case é avaliado. Você pode ACRESCENTAR
conferências novas; não relaxe nem remova as existentes.

Toda conferência aqui SINALIZA uma divergência; nenhuma jamais bloqueia a
escrita. O PDF de origem às vezes simplesmente não fecha (arredondamento, uma
linha omitida), e recusar guardar o que o próprio documento do cliente diz
tornaria o app inútil — pior, empurraria quem preenche a amassar números até a
API aceitar. Um sistema de registro que empurra seu operador para falsificar
dado falhou na sua única função.

Só FOLHAS somam: uma conta presente conta para um total apenas se nenhum
descendente dela ESTIVER TAMBÉM presente nesta demonstração — um pai presente é
sempre conferência contra a soma dos filhos, nunca uma parcela. É isso que faz
"o PDF imprime o total E a quebra" sair de graça, em vez de virar uma
duplicação silenciosa.
"""

from decimal import Decimal

from credit.financials.models.account_chart import AccountChart
from credit.financials.models.statement import FinancialStatement

_TOLERANCE_ABS = Decimal("0.05")
_TOLERANCE_REL = Decimal("0.0001")

#: Lucro/Prejuízo Líquido do Exercício — a única linha RESULT contra a qual o
#: fechamento é conferido. Subtotais intermediários (Lucro Bruto, EBIT, ...)
#: não são modelados: suas fórmulas envolvem escolhas de domínio (o que conta
#: como "operacional") que este service não faz.
_RESULT_LIQUIDO_CODE = "6.05"

#: Tipos que quase nunca são legitimamente negativos numa linha folha. EQUITY
#: (Lucros/Prejuízos Acumulados rotineiramente negativo) e EXPENSE (estorno
#: ocasional) ficam de fora de propósito — sinalizá-los seria falso positivo em
#: caso comum e legítimo.
_SIGN_SENSITIVE_TYPES = {
    AccountChart.TYPE_ASSET,
    AccountChart.TYPE_LIABILITY,
    AccountChart.TYPE_REVENUE,
}


def _is_close(a: Decimal, b: Decimal) -> bool:
    diff = abs(a - b)
    tolerance = max(_TOLERANCE_ABS, _TOLERANCE_REL * max(abs(a), abs(b)))
    return diff <= tolerance


def _leaf_codes(present: set) -> set:
    """Um código presente é folha se e somente se nenhum OUTRO código presente
    for descendente dele (um código pontuado prefixado por ``code + "."``)."""
    leaves = set()
    for code in present:
        prefix = f"{code}."
        if not any(other.startswith(prefix) for other in present if other != code):
            leaves.add(code)
    return leaves


def _sum_by_type(codes, by_code, value_by_code, account_type) -> Decimal:
    return sum(
        (value_by_code[c] for c in codes if by_code[c].account_type == account_type),
        Decimal(0),
    )


def _balance_sheet_equation(leaves, by_code, value_by_code) -> dict:
    assets = _sum_by_type(leaves, by_code, value_by_code, AccountChart.TYPE_ASSET)
    liabilities = _sum_by_type(
        leaves, by_code, value_by_code, AccountChart.TYPE_LIABILITY
    )
    equity = _sum_by_type(leaves, by_code, value_by_code, AccountChart.TYPE_EQUITY)
    expected = liabilities + equity
    ok = _is_close(assets, expected)
    return {
        "check": "BALANCE_SHEET_EQUATION",
        "status": "PASS" if ok else "FAIL",
        "severity": "WARNING",
        "message": (
            "Ativo bate com Passivo + PL."
            if ok
            else f"Ativo ({assets}) difere de Passivo + PL ({expected})."
        ),
        "expected": str(expected),
        "actual": str(assets),
        "discrepancy": str(assets - expected),
    }


def _income_statement_footing(leaves, by_code, value_by_code) -> dict | None:
    if _RESULT_LIQUIDO_CODE not in value_by_code:
        return None
    revenue = _sum_by_type(leaves, by_code, value_by_code, AccountChart.TYPE_REVENUE)
    expense = _sum_by_type(leaves, by_code, value_by_code, AccountChart.TYPE_EXPENSE)
    computed = revenue - expense
    printed = value_by_code[_RESULT_LIQUIDO_CODE]
    ok = _is_close(computed, printed)
    return {
        "check": "INCOME_STATEMENT_FOOTING",
        "status": "PASS" if ok else "FAIL",
        "severity": "WARNING",
        "message": (
            "Receitas - Despesas bate com o Lucro Líquido informado."
            if ok
            else (
                f"Receitas - Despesas ({computed}) difere do Lucro Líquido "
                f"informado ({printed})."
            )
        ),
        "expected": str(computed),
        "actual": str(printed),
        "discrepancy": str(printed - computed),
    }


def _subtotal_checks(present, leaves, by_code, value_by_code) -> list:
    """Qualquer não-folha presente contra a soma dos seus filhos DIRETOS
    presentes. Pulado em silêncio quando nenhum filho está presente — isso
    significa que só o subtotal foi enviado, sem quebra, o que não é
    divergência a sinalizar."""
    checks = []
    for code in sorted(present - leaves):
        children_present = [c for c in present if by_code[c].parent_id == code]
        if not children_present:
            continue
        children_sum = sum((value_by_code[c] for c in children_present), Decimal(0))
        printed = value_by_code[code]
        if not _is_close(children_sum, printed):
            checks.append(
                {
                    "check": "SUBTOTAL_MISMATCH",
                    "status": "FAIL",
                    "severity": "WARNING",
                    "message": (
                        f"'{code}' informado como {printed}, mas os filhos "
                        f"somam {children_sum}."
                    ),
                    "account_code": code,
                    "expected": str(children_sum),
                    "actual": str(printed),
                    "discrepancy": str(printed - children_sum),
                }
            )
    return checks


def _sign_checks(leaves, by_code, value_by_code) -> list:
    checks = []
    for code in sorted(leaves):
        account = by_code[code]
        if account.account_type in _SIGN_SENSITIVE_TYPES and value_by_code[code] < 0:
            checks.append(
                {
                    "check": "SIGN_CONVENTION",
                    "status": "FAIL",
                    "severity": "WARNING",
                    "message": (
                        f"'{code}' ({account.account_type}) está negativo — "
                        "fora da convenção para este tipo de conta."
                    ),
                    "account_code": code,
                    "actual": str(value_by_code[code]),
                }
            )
    return checks


def run_checks(statement_type: str, lines: list) -> list:
    """``lines``: ``[{"account": <AccountChart>, "value": Decimal, ...}]`` — o
    formato que ``statement_service`` já monta depois de validar que a conta de
    cada linha existe e casa com ``statement_type``.

    Devolve uma lista de ``{check, status, severity, message, ...}``. Nunca
    levanta exceção, e nunca use "lista vazia" como sinônimo de aprovado: leia
    o campo ``status``.
    """
    by_code = {line["account"].account_code: line["account"] for line in lines}
    value_by_code = {line["account"].account_code: line["value"] for line in lines}
    present = set(by_code)
    leaves = _leaf_codes(present)

    checks = []
    checks.extend(_subtotal_checks(present, leaves, by_code, value_by_code))
    checks.extend(_sign_checks(leaves, by_code, value_by_code))

    if statement_type == FinancialStatement.TYPE_BALANCE_SHEET:
        checks.append(_balance_sheet_equation(leaves, by_code, value_by_code))
    elif statement_type == FinancialStatement.TYPE_INCOME_STATEMENT:
        footing = _income_statement_footing(leaves, by_code, value_by_code)
        if footing is not None:
            checks.append(footing)

    return checks
