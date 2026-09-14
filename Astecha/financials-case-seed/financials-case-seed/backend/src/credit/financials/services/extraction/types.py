"""Os tipos que atravessam o pipeline de extração.

São dataclasses puras: nada de Django, nada de ORM, nada de I/O. Isso é de
propósito — o provider tem que ser testável sem banco e sem rede, e o mesmo
tipo tem que valer para o provider baseado em regra e para o baseado em LLM.

    arquivo -> ParsedDocument -> ExtractionProvider.extract() -> StatementDraft

``StatementDraft`` é o formato canônico do rascunho. Quando o analista aprova,
o seu código converte o draft no payload de
``statement_service.write_statements`` — que é o caminho de escrita da
plataforma. Faça a conversão num único lugar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class ParsedTable:
    """Uma tabela achada no documento, já em linhas/colunas de texto cru."""

    page: int
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """A saída do parse, ANTES de qualquer interpretação contábil.

    Nada aqui está normalizado ainda: ``text`` e ``tables`` são o que estava no
    papel. É a matéria-prima que o provider recebe.
    """

    document_id: int
    file_type: str
    text: str = ""
    tables: list[ParsedTable] = field(default_factory=list)
    page_count: int = 0


@dataclass
class DraftLine:
    """Uma linha do rascunho.

    ``raw_label`` / ``raw_value`` são o que o documento dizia, LITERALMENTE —
    nunca sobrescreva com o valor já convertido. É o que permite conferir o
    de-para e é o que vai para ``FinancialStatementLine.raw_label``.

    ``value`` é o número final, já com a escala aplicada e o sinal na convenção
    de destino (DESPESA positiva).

    ``confidence`` é 0.0 a 1.0. Calibre: se você marcar 0.95 em tudo, o revisor
    perde a única informação que diz onde olhar primeiro, e o critério de
    avaliação nº 4 cai junto.
    """

    raw_label: str
    raw_value: str
    value: Decimal | None = None
    account_code: str | None = None
    confidence: float = 0.0
    page: int | None = None
    notes: str | None = None


@dataclass
class StatementDraft:
    """Uma demonstração rascunhada. UM documento pode gerar VÁRIAS: um balanço
    costuma trazer duas colunas de período (31/12/2025 e 31/12/2024), e cada
    coluna é uma demonstração diferente. Não misture as duas num draft só."""

    statement_type: str  # BALANCE_SHEET | INCOME_STATEMENT
    period_end_date: date | None
    period_type: str | None  # MONTHLY | QUARTERLY | ANNUAL
    currency: str = "BRL"
    scale_factor: int = 1  # 1 | 1_000 | 1_000_000 — o "Em R$ mil" do cabeçalho
    lines: list[DraftLine] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """O que um provider devolve para UM documento."""

    drafts: list[StatementDraft] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    prompt_version: str = ""
    latency_ms: int = 0
    cost_usd: float = 0.0
    warnings: list[str] = field(default_factory=list)
