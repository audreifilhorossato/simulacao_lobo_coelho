"""Conferências contábeis — funções puras, testadas sem banco.

Repare que estes testes NÃO têm ``@pytest.mark.django_db``: o
``checks_service`` não toca o ORM, e é por isso que ele roda em milissegundos.
Mantenha assim quando acrescentar conferências suas.
"""

from decimal import Decimal
from types import SimpleNamespace

from credit.financials.services import checks_service


def _line(code, tipo, valor, parent=None):
    """Uma AccountChart falsa — o service só lê ``account_code``,
    ``account_type`` e ``parent_id``, então não é preciso banco."""
    return {
        "account": SimpleNamespace(
            account_code=code, account_type=tipo, parent_id=parent
        ),
        "value": Decimal(valor),
        "raw_label": code,
    }


def _by_check(checks, name):
    return next((c for c in checks if c["check"] == name), None)


def test_balanco_que_fecha_passa():
    checks = checks_service.run_checks(
        "BALANCE_SHEET",
        [
            _line("1.01.01", "ASSET", "1000"),
            _line("2.01.01", "LIABILITY", "600"),
            _line("3.01", "EQUITY", "400"),
        ],
    )
    assert _by_check(checks, "BALANCE_SHEET_EQUATION")["status"] == "PASS"


def test_balanco_que_nao_fecha_sinaliza_mas_nao_levanta():
    checks = checks_service.run_checks(
        "BALANCE_SHEET",
        [
            _line("1.01.01", "ASSET", "1000"),
            _line("2.01.01", "LIABILITY", "600"),
            _line("3.01", "EQUITY", "300"),
        ],
    )
    check = _by_check(checks, "BALANCE_SHEET_EQUATION")
    assert check["status"] == "FAIL"
    assert check["discrepancy"] == "100"


def test_pai_presente_nao_soma_junto_com_os_filhos():
    """O caso que faz todo mundo errar por 2x: o PDF imprime 'Ativo Circulante
    1000' E as contas que somam 1000. Se as duas coisas somarem, o ativo vira
    2000 e o balanco 'nao fecha' por um bug seu, nao do documento."""
    checks = checks_service.run_checks(
        "BALANCE_SHEET",
        [
            _line("1.01", "ASSET", "1000"),
            _line("1.01.01", "ASSET", "600", parent="1.01"),
            _line("1.01.02", "ASSET", "400", parent="1.01"),
            _line("2.01.01", "LIABILITY", "1000"),
        ],
    )
    equacao = _by_check(checks, "BALANCE_SHEET_EQUATION")
    assert equacao["status"] == "PASS", "o pai foi somado junto com os filhos"
    assert _by_check(checks, "SUBTOTAL_MISMATCH") is None


def test_subtotal_que_nao_bate_com_os_filhos_e_sinalizado():
    checks = checks_service.run_checks(
        "BALANCE_SHEET",
        [
            _line("1.01", "ASSET", "999"),
            _line("1.01.01", "ASSET", "600", parent="1.01"),
            _line("1.01.02", "ASSET", "400", parent="1.01"),
        ],
    )
    assert _by_check(checks, "SUBTOTAL_MISMATCH")["status"] == "FAIL"


def test_dre_fecha_contra_o_lucro_impresso():
    checks = checks_service.run_checks(
        "INCOME_STATEMENT",
        [
            _line("4.01", "REVENUE", "1000"),
            _line("5.01", "EXPENSE", "700"),
            _line("6.05", "RESULT", "300"),
        ],
    )
    assert _by_check(checks, "INCOME_STATEMENT_FOOTING")["status"] == "PASS"


def test_despesa_com_sinal_invertido_derruba_o_fechamento():
    """A convencao de destino e DESPESA POSITIVA. Mandar -700 faz a conta virar
    1000 - (-700) = 1700 e o fechamento acusar. E o sintoma numero 1 de sinal
    lido errado do PDF."""
    checks = checks_service.run_checks(
        "INCOME_STATEMENT",
        [
            _line("4.01", "REVENUE", "1000"),
            _line("5.01", "EXPENSE", "-700"),
            _line("6.05", "RESULT", "300"),
        ],
    )
    assert _by_check(checks, "INCOME_STATEMENT_FOOTING")["status"] == "FAIL"


def test_receita_negativa_e_sinalizada():
    checks = checks_service.run_checks(
        "INCOME_STATEMENT", [_line("4.01", "REVENUE", "-10")]
    )
    assert _by_check(checks, "SIGN_CONVENTION")["status"] == "FAIL"


def test_nenhuma_conferencia_levanta_excecao_com_lista_vazia():
    assert checks_service.run_checks("BALANCE_SHEET", []) is not None
