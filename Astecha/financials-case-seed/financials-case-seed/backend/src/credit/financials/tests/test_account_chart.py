"""O plano de contas semeado — o teste que prova que a migration 0002 rodou.

Modelo de como escrever os seus: um arquivo por recurso, HTTP de verdade via
APIClient, e cada teste com um nome que diz o que ele garante.
"""

import pytest
from credit.financials.models import AccountChart


@pytest.mark.django_db
def test_seed_criou_as_59_contas_padrao():
    assert AccountChart.objects.filter(origin="STANDARD").count() == 59


@pytest.mark.django_db
def test_toda_conta_tem_pai_existente():
    """Nenhuma conta orfa: se o pai nao existe, a arvore nao renderiza e o
    checks_service nao consegue conferir subtotal contra filhos."""
    codes = set(AccountChart.objects.values_list("account_code", flat=True))
    orphans = [
        a.account_code
        for a in AccountChart.objects.exclude(parent_id=None)
        if a.parent_id not in codes
    ]
    assert orphans == []


@pytest.mark.django_db
def test_tipo_e_derivado_do_grupo_do_codigo():
    """Uma DESPESA pendurada no ATIVO tem que ser irrepresentavel."""
    for account in AccountChart.objects.all():
        grupo = account.account_code.split(".")[0]
        esperado = {
            "1": "ASSET",
            "2": "LIABILITY",
            "3": "EQUITY",
            "4": "REVENUE",
            "5": "EXPENSE",
            "6": "RESULT",
        }[grupo]
        assert account.account_type == esperado, account.account_code


@pytest.mark.django_db
def test_lista_o_plano_pela_api(api):
    resp = api.get("/api/v1/credit/financials/account-chart?page_size=500")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 59
    # Chaves em MAIUSCULA — o contrato com o frontend da plataforma.
    assert "ACCOUNT_CODE" in body["results"][0]


@pytest.mark.django_db
def test_filtra_por_statement(api):
    resp = api.get(
        "/api/v1/credit/financials/account-chart"
        "?statement=INCOME_STATEMENT&page_size=500"
    )
    assert resp.status_code == 200
    assert {r["STATEMENT"] for r in resp.json()["results"]} == {"INCOME_STATEMENT"}


@pytest.mark.django_db
def test_conta_padrao_nao_pode_ser_alterada(api):
    """Regra que protege a comparabilidade: se um cliente puder redefinir
    '1.01.01', duas empresas deixam de ser comparaveis em silencio."""
    resp = api.post(
        "/api/v1/credit/financials/account-chart/upsert",
        {"ACCOUNT_CODE": "1.01.01", "ACCOUNT_NAME": "Meu caixa"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["errors"], "esperava erro de conta STANDARD imutavel"


@pytest.mark.django_db
def test_cria_conta_custom_sob_uma_padrao(api):
    resp = api.post(
        "/api/v1/credit/financials/account-chart/upsert",
        {"ACCOUNT_CODE": "1.01.01.01", "ACCOUNT_NAME": "Caixa - Banco X"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    assert resp.json()["errors"] == []
    nova = AccountChart.objects.get(account_code="1.01.01.01")
    assert nova.origin == "CUSTOM"
    assert nova.level == 4
    assert nova.parent_id == "1.01.01"
    # Tipo e statement herdados do grupo, nao do payload.
    assert nova.account_type == "ASSET"
