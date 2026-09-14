"""Upload do documento bruto."""

import pytest
from credit.financials.models import SourceDocument
from credit.financials.services import storage
from django.core.files.uploadedfile import SimpleUploadedFile

URL = "/api/v1/credit/financials/documents/upload"


@pytest.fixture(autouse=True)
def _limpa_storage():
    storage.purge_all()
    yield
    storage.purge_all()


def _pdf(nome="balanco.pdf"):
    return SimpleUploadedFile(
        nome, b"%PDF-1.4 conteudo", content_type="application/pdf"
    )


@pytest.mark.django_db
def test_upload_registra_documento_pendente(api, company):
    resp = api.post(
        URL,
        {"company_id": company.id, "year": 2025, "month": 12, "file": _pdf()},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["PROCESSING_STATUS"] == "PENDING"
    assert body["STAGE_PATH"] == f"{company.id}/2025/12/balanco.pdf"
    assert body["FILE_TYPE"] == "PDF"


@pytest.mark.django_db
def test_upload_grava_o_arquivo_de_verdade(api, company):
    api.post(
        URL,
        {"company_id": company.id, "year": 2025, "month": 12, "file": _pdf()},
        format="multipart",
    )
    assert storage.get_file(company.id, 2025, 12, "balanco.pdf").startswith(b"%PDF")


@pytest.mark.django_db
def test_reenviar_o_mesmo_arquivo_nao_cria_documento_duplicado(api, company):
    """O caminho e a chave. Dois registros apontando para o mesmo arquivo
    fariam a metrica de acuracia contar o mesmo documento duas vezes."""
    for _ in range(2):
        api.post(
            URL,
            {"company_id": company.id, "year": 2025, "month": 12, "file": _pdf()},
            format="multipart",
        )
    assert SourceDocument.objects.count() == 1


@pytest.mark.django_db
def test_empresa_inexistente_e_recusada(api):
    resp = api.post(
        URL,
        {"company_id": 99999, "year": 2025, "month": 12, "file": _pdf()},
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_formato_nao_suportado_e_recusado(api, company):
    arquivo = SimpleUploadedFile("nota.txt", b"texto", content_type="text/plain")
    resp = api.post(
        URL,
        {"company_id": company.id, "year": 2025, "month": 12, "file": arquivo},
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_competencia_invalida_e_recusada(api, company):
    resp = api.post(
        URL,
        {"company_id": company.id, "year": 2025, "month": 13, "file": _pdf()},
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_documentos_nao_aceitam_escrita_generica(api):
    """A criacao e so pelo /upload — um POST cru na colecao nao pode existir,
    senao da para registrar documento sem arquivo nenhum por tras."""
    assert api.post("/api/v1/credit/financials/documents", {}).status_code == 405
