"""O plano de contas padronizado brasileiro (Lei 6.404/76 + CPC 26).

PORTADO VERBATIM da plataforma Astecha. Semente da migration 0002.

Formato: lista ORDENADA de ``(account_code, account_name)``. Todo o resto é
DERIVADO:

- ``level`` / ``parent`` a partir do código pontuado (``account_chart_service.derive``);
- ``account_type`` / ``statement`` a partir do grupo de nível 1 em ``GROUPS``;
- ``display_order`` a partir da posição nesta lista (x 10, deixando espaço para
  inserir contas CUSTOM entre duas padrão depois).

Derivar em vez de repetir é deliberado: uma coluna ``account_type`` por linha
tornaria representável "uma DESPESA pendurada no ATIVO", e cedo ou tarde
alguém digitaria isso. Aqui não dá nem para expressar.

A profundidade é de 3 níveis (grupo -> subgrupo -> conta). Mais fundo que isso
e a taxonomia deixa de ser comparável entre empresas, que é a única razão de
ela ser global. Granularidade extra é conta CUSTOM de nível 4.

Códigos terminados em ``.09``/``.9`` são a válvula de escape "Outros",
deliberada: uma linha que não casa com nada ainda tem uma casa honesta, em vez
de ser empurrada para uma conta específica à qual não pertence.
"""

from credit.financials.models.account_chart import AccountChart

_BS = AccountChart.STATEMENT_BALANCE_SHEET
_IS = AccountChart.STATEMENT_INCOME_STATEMENT

#: Grupo de nível 1 -> (account_type, statement). O ÚNICO lugar em que um tipo
#: é declarado.
GROUPS = {
    "1": (AccountChart.TYPE_ASSET, _BS),
    "2": (AccountChart.TYPE_LIABILITY, _BS),
    "3": (AccountChart.TYPE_EQUITY, _BS),
    "4": (AccountChart.TYPE_REVENUE, _IS),
    "5": (AccountChart.TYPE_EXPENSE, _IS),
    "6": (AccountChart.TYPE_RESULT, _IS),
}

#: ``(account_code, account_name)`` em ordem. A ordem define ``display_order``.
STANDARD_CHART = [
    # -- 1 Ativo --------------------------------------------------------------
    ("1", "Ativo"),
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Contas a Receber de Clientes"),
    ("1.01.04", "Estoques"),
    ("1.01.05", "Tributos a Recuperar"),
    ("1.01.06", "Adiantamentos"),
    ("1.01.09", "Outros Ativos Circulantes"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
    ("1.02.09", "Outros Ativos Não Circulantes"),
    # -- 2 Passivo ------------------------------------------------------------
    ("2", "Passivo"),
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Fornecedores"),
    ("2.01.02", "Empréstimos e Financiamentos"),
    ("2.01.03", "Obrigações Trabalhistas e Previdenciárias"),
    ("2.01.04", "Obrigações Fiscais"),
    ("2.01.05", "Dividendos e JCP a Pagar"),
    ("2.01.06", "Adiantamentos de Clientes"),
    ("2.01.09", "Outros Passivos Circulantes"),
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Empréstimos e Financiamentos de Longo Prazo"),
    ("2.02.02", "Debêntures"),
    ("2.02.03", "Provisões"),
    ("2.02.04", "Tributos Diferidos"),
    ("2.02.09", "Outros Passivos Não Circulantes"),
    # -- 3 Patrimônio Líquido -------------------------------------------------
    ("3", "Patrimônio Líquido"),
    ("3.01", "Capital Social"),
    ("3.02", "Reservas de Capital"),
    ("3.03", "Reservas de Lucros"),
    ("3.04", "Ajustes de Avaliação Patrimonial"),
    ("3.05", "Lucros ou Prejuízos Acumulados"),
    ("3.06", "Ações em Tesouraria"),
    ("3.07", "Participação de Não Controladores"),
    ("3.09", "Outras Contas do Patrimônio Líquido"),
    # -- 4 Receitas -----------------------------------------------------------
    ("4", "Receitas"),
    ("4.01", "Receita Bruta de Vendas e Serviços"),
    ("4.02", "Deduções da Receita Bruta"),
    ("4.03", "Receitas Financeiras"),
    ("4.04", "Resultado de Equivalência Patrimonial"),
    ("4.09", "Outras Receitas Operacionais"),
    # -- 5 Custos e Despesas --------------------------------------------------
    ("5", "Custos e Despesas"),
    ("5.01", "Custo dos Produtos e Serviços Vendidos"),
    ("5.02", "Despesas com Vendas"),
    ("5.03", "Despesas Gerais e Administrativas"),
    ("5.04", "Depreciação e Amortização"),
    ("5.05", "Despesas Financeiras"),
    ("5.06", "Imposto de Renda e Contribuição Social"),
    ("5.09", "Outras Despesas Operacionais"),
    # -- 6 Resultado (subtotais impressos na DRE) -----------------------------
    ("6", "Resultado"),
    ("6.01", "Receita Líquida"),
    ("6.02", "Lucro Bruto"),
    ("6.03", "Resultado Operacional (EBIT)"),
    ("6.04", "Resultado Antes do IR e CSLL"),
    ("6.05", "Lucro ou Prejuízo Líquido do Exercício"),
]
