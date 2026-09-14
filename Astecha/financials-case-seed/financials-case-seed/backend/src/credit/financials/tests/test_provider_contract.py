"""O contrato do provider de extração — a costura de migração nº 2.

**Todo provider que vocês escreverem tem que passar por estes testes.**
Acrescente o nome do seu provider em ``PROVIDERS`` e mais nada: se ele quebrar
aqui, ele quebra a migração.

Repare que nenhum teste toca banco nem rede. Se o seu provider precisar de
banco para funcionar, ele está fazendo coisa demais: separe o que é extração do
que é persistência.
"""

import pytest
from credit.financials.services.extraction import providers
from credit.financials.services.extraction.providers.base import ExtractionProvider
from credit.financials.services.extraction.types import (
    ExtractionResult,
    ParsedDocument,
)

#: Acrescente os seus aqui: "rule_based" (Sprint 1), "llm" (Sprint 3).
#: O "llm" só entra quando houver um modo offline/mock — teste que chama API
#: paga não pode rodar no CI.
PROVIDERS = ["naive"]


@pytest.fixture
def documento_vazio():
    return ParsedDocument(document_id=1, file_type="PDF", text="", page_count=0)


@pytest.fixture
def documento_lixo():
    return ParsedDocument(
        document_id=2,
        file_type="PDF",
        text="\x00\x01 rabisco ilegivel |||| ,,,, ---- 39u2h39",
        page_count=1,
    )


@pytest.mark.parametrize("name", PROVIDERS)
def test_provider_satisfaz_a_interface(name):
    assert isinstance(providers.get_provider(name), ExtractionProvider)


@pytest.mark.parametrize("name", PROVIDERS)
def test_provider_tem_nome_estavel(name):
    assert providers.get_provider(name).name == name


@pytest.mark.parametrize("name", PROVIDERS)
def test_documento_vazio_nao_levanta_excecao(name, documento_vazio):
    """Documento que nao deu para ler devolve drafts=[] e o motivo em
    warnings. Nunca uma excecao: um PDF ruim no meio de um lote nao pode
    derrubar o lote inteiro."""
    result = providers.get_provider(name).extract(documento_vazio)
    assert isinstance(result, ExtractionResult)
    assert result.drafts == []
    assert result.warnings


@pytest.mark.parametrize("name", PROVIDERS)
def test_documento_ilegivel_nao_levanta_excecao(name, documento_lixo):
    assert isinstance(
        providers.get_provider(name).extract(documento_lixo), ExtractionResult
    )


@pytest.mark.parametrize("name", PROVIDERS)
def test_mesma_entrada_produz_a_mesma_saida(name, documento_lixo):
    """Determinismo. Com LLM isso significa temperature=0 — sem ele a metrica
    de acuracia vira ruido e voce nao consegue provar melhora nenhuma."""
    provider = providers.get_provider(name)
    a = provider.extract(documento_lixo)
    b = provider.extract(documento_lixo)
    assert len(a.drafts) == len(b.drafts)


def test_nome_desconhecido_falha_alto_com_a_lista_do_que_existe():
    """Um typo no .env nao pode cair num default silencioso: a metrica passaria
    a medir outro provider sem ninguem perceber."""
    with pytest.raises(ValueError) as exc:
        providers.get_provider("provider-que-nao-existe")
    assert "naive" in str(exc.value)


def test_naive_e_o_piso_e_nao_extrai_nada(documento_lixo):
    """Controle do arreio de avaliacao: se um dia o seu rule_based empatar com
    este, o defeito esta no arreio, nao no provider."""
    assert providers.get_provider("naive").extract(documento_lixo).drafts == []
