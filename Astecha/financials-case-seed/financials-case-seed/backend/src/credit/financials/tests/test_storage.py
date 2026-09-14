"""Armazenamento — a costura de migração nº 1.

Estes testes existem para travar a ASSINATURA e o LAYOUT DE CAMINHO. Eles têm
que continuar passando depois que a Astecha trocar a implementação pelo stage do
Snowflake; se você mudar uma assinatura para "ficar mais bonito", quebra a
migração e reprova no critério nº 2.
"""

import pytest
from credit.financials.services import storage


@pytest.fixture(autouse=True)
def _limpa_storage():
    storage.purge_all()
    yield
    storage.purge_all()


def test_layout_do_caminho_e_company_ano_mes():
    assert storage.folder_path(7, 2025, 3) == "7/2025/03"


def test_mes_de_um_digito_e_zero_a_esquerda():
    """'2025/3' e '2025/03' seriam duas pastas diferentes no stage. Zero a
    esquerda nao e estetica: e o que evita o acervo se partir em dois."""
    assert storage.folder_path(1, 2025, 3).endswith("/03")


def test_ano_fora_da_faixa_e_recusado():
    with pytest.raises(ValueError):
        storage.folder_path(1, 1899, 1)


def test_mes_invalido_e_recusado():
    with pytest.raises(ValueError):
        storage.folder_path(1, 2025, 13)


def test_put_devolve_caminho_relativo_e_get_le_de_volta():
    rel = storage.put_file(b"conteudo", 42, 2025, 12, "balanco.pdf")
    assert rel == "42/2025/12/balanco.pdf"
    assert storage.get_file(42, 2025, 12, "balanco.pdf") == b"conteudo"


def test_nome_com_traversal_e_neutralizado():
    """Um upload chamado '../../etc/passwd' nao pode escapar da pasta."""
    rel = storage.put_file(b"x", 1, 2025, 1, "../../etc/passwd")
    assert rel == "1/2025/01/passwd"


def test_list_devolve_vazio_quando_a_pasta_nao_existe():
    """Ausencia nao e erro — o LIST do Snowflake se comporta igual."""
    assert storage.list_files(999, 2030, 1) == []


def test_list_enumera_o_que_foi_gravado():
    storage.put_file(b"a", 1, 2025, 1, "b.pdf")
    storage.put_file(b"aa", 1, 2025, 1, "a.pdf")
    files = storage.list_files(1, 2025, 1)
    assert [f["file_name"] for f in files] == ["a.pdf", "b.pdf"]
    assert files[0]["relative_path"] == "1/2025/01/a.pdf"


def test_remove_apaga_e_devolve_o_caminho():
    storage.put_file(b"x", 1, 2025, 1, "a.pdf")
    assert storage.remove_file(1, 2025, 1, "a.pdf") == "1/2025/01/a.pdf"
    assert storage.list_files(1, 2025, 1) == []


def test_get_de_arquivo_ausente_levanta_filenotfound():
    with pytest.raises(FileNotFoundError):
        storage.get_file(1, 2025, 1, "nao-existe.pdf")
