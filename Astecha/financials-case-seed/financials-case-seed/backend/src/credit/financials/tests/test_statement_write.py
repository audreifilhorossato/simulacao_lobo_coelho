"""O caminho de escrita — o alvo do pipeline de vocês.

Quando o analista aprova um rascunho, é ESTE endpoint que o seu código chama.
Estes testes fixam o contrato; não os afrouxe para o seu rascunho passar.
"""

import pytest
from credit.financials.models import FinancialStatement, FinancialStatementLine

URL_WRITE = "/api/v1/credit/financials/statements/write"
URL_VALIDATE = "/api/v1/credit/financials/statements/validate"


def _payload(company, balanco_valido):
    payload = dict(balanco_valido)
    payload["company_id"] = company.id
    return payload


@pytest.mark.django_db
def test_escreve_balanco_e_linhas(api, company, balanco_valido):
    resp = api.post(URL_WRITE, _payload(company, balanco_valido), format="json")
    assert resp.status_code == 200, resp.content
    result = resp.json()["results"][0]
    assert result["created"] is True
    assert result["line_count"] == 3
    assert FinancialStatementLine.objects.count() == 3


@pytest.mark.django_db
def test_reenviar_o_mesmo_payload_converge_em_vez_de_duplicar(
    api, company, balanco_valido
):
    """Idempotencia pela chave natural (empresa, tipo, competencia). E o que
    torna seguro reenviar depois de um timeout de rede."""
    payload = _payload(company, balanco_valido)
    first = api.post(URL_WRITE, payload, format="json").json()["results"][0]
    second = api.post(URL_WRITE, payload, format="json").json()["results"][0]

    assert first["statement_id"] == second["statement_id"]
    assert second["created"] is False
    assert FinancialStatement.objects.count() == 1
    assert FinancialStatementLine.objects.count() == 3


@pytest.mark.django_db
def test_reenvio_sem_uma_linha_remove_a_linha(api, company, balanco_valido):
    """Substituicao total, nunca merge: um merge nao consegue expressar 'esta
    linha foi removida' e deixaria uma linha fantasma somando para sempre."""
    payload = _payload(company, balanco_valido)
    api.post(URL_WRITE, payload, format="json")

    payload["statements"][0]["lines"] = payload["statements"][0]["lines"][:2]
    api.post(URL_WRITE, payload, format="json")

    assert FinancialStatementLine.objects.count() == 2


@pytest.mark.django_db
def test_conta_inexistente_recusa_o_lote_inteiro(api, company, balanco_valido):
    payload = _payload(company, balanco_valido)
    payload["statements"][0]["lines"].append(
        {"account_code": "9.99", "raw_label": "Invencao", "value": "1.00"}
    )
    resp = api.post(URL_WRITE, payload, format="json")
    assert resp.status_code == 400
    assert FinancialStatement.objects.count() == 0, "nada podia ter sido escrito"


@pytest.mark.django_db
def test_conta_repetida_na_mesma_demonstracao_e_recusada(api, company, balanco_valido):
    payload = _payload(company, balanco_valido)
    payload["statements"][0]["lines"].append(
        {"account_code": "1.01.01", "raw_label": "Caixa de novo", "value": "5.00"}
    )
    assert api.post(URL_WRITE, payload, format="json").status_code == 400


@pytest.mark.django_db
def test_data_que_nao_e_fim_de_mes_e_recusada(api, company, balanco_valido):
    """PERIOD_END_DATE e sempre o ultimo dia do mes. Um '2025-12-30' vindo do
    OCR e erro de leitura, nao uma competencia nova."""
    payload = _payload(company, balanco_valido)
    payload["statements"][0]["period_end_date"] = "2025-12-30"
    assert api.post(URL_WRITE, payload, format="json").status_code == 400


@pytest.mark.django_db
def test_conta_de_dre_num_balanco_e_recusada(api, company, balanco_valido):
    payload = _payload(company, balanco_valido)
    payload["statements"][0]["lines"].append(
        {"account_code": "4.01", "raw_label": "Receita", "value": "10.00"}
    )
    assert api.post(URL_WRITE, payload, format="json").status_code == 400


@pytest.mark.django_db
def test_validate_nao_escreve_nada(api, company, balanco_valido):
    resp = api.post(URL_VALIDATE, _payload(company, balanco_valido), format="json")
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "ready"
    assert FinancialStatement.objects.count() == 0


@pytest.mark.django_db
def test_validate_reporta_erro_como_dado_e_nao_como_400(api, company, balanco_valido):
    payload = _payload(company, balanco_valido)
    payload["statements"][0]["lines"][0]["account_code"] = "9.99"
    resp = api.post(URL_VALIDATE, payload, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "action_required"
    assert body["errors"]


@pytest.mark.django_db
def test_checks_vem_junto_com_a_escrita(api, company, balanco_valido):
    resp = api.post(URL_WRITE, _payload(company, balanco_valido), format="json")
    checks = resp.json()["results"][0]["checks"]
    equacao = next(c for c in checks if c["check"] == "BALANCE_SHEET_EQUATION")
    assert equacao["status"] == "PASS"


@pytest.mark.django_db
def test_balanco_que_nao_fecha_ainda_assim_e_gravado(api, company, balanco_valido):
    """Regra de produto, nao descuido: o documento do cliente as vezes nao
    fecha. Recusar a escrita empurraria o operador a amassar numero ate a API
    aceitar — e ai o sistema de registro passa a mentir."""
    payload = _payload(company, balanco_valido)
    payload["statements"][0]["lines"][2]["value"] = "300.00"
    resp = api.post(URL_WRITE, payload, format="json")

    assert resp.status_code == 200
    assert FinancialStatement.objects.count() == 1
    checks = resp.json()["results"][0]["checks"]
    equacao = next(c for c in checks if c["check"] == "BALANCE_SHEET_EQUATION")
    assert equacao["status"] == "FAIL"
