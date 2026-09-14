"""Cadastro de empresas."""

import pytest

URL = "/api/v1/credit/financials/companies"


@pytest.mark.django_db
def test_cria_empresa(api):
    resp = api.post(
        URL, {"NAME": "Alfa Industria SA", "CNPJ": "11.222.333/0001-81"}, format="json"
    )
    assert resp.status_code == 201, resp.content
    # CNPJ normalizado para 14 digitos, sem mascara.
    assert resp.json()["CNPJ"] == "11222333000181"


@pytest.mark.django_db
def test_cnpj_com_numero_errado_de_digitos_e_recusado(api):
    resp = api.post(URL, {"NAME": "Beta", "CNPJ": "123"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cnpj_duplicado_e_recusado(api, company):
    resp = api.post(URL, {"NAME": "Outra", "CNPJ": company.cnpj}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_lista_paginada_no_envelope_padrao(api, company):
    body = api.get(URL).json()
    assert set(body) >= {"count", "next", "previous", "results"}
    assert body["count"] == 1


@pytest.mark.django_db
def test_busca_por_nome(api, company):
    assert api.get(f"{URL}?search=Exemplo").json()["count"] == 1
    assert api.get(f"{URL}?search=Inexistente").json()["count"] == 0


@pytest.mark.django_db
def test_lista_vazia_nao_quebra(api):
    body = api.get(URL).json()
    assert body["count"] == 0
    assert body["results"] == []
