"""Plano de contas padronizado — a taxonomia única em que TODA linha de balanço
e de DRE tem que cair, venha o documento no formato que vier.

PORTADO VERBATIM da plataforma Astecha.

Global, não por empresa: é isso que torna duas empresas comparáveis, e é o
motivo inteiro de padronizar. A migration 0002 semeia o padrão brasileiro
(Lei 6.404/76 + CPC 26) como ORIGIN='STANDARD' — 59 contas, 3 níveis.

Extensão: uma conta mais profunda pode ser criada como ORIGIN='CUSTOM' filha de
uma existente. Linhas STANDARD são imutáveis pela API (409), para que a
extensão de um cliente nunca redefina em silêncio a taxonomia compartilhada.
"""

from django.db import models


class AccountChart(models.Model):
    TYPE_ASSET = "ASSET"
    TYPE_LIABILITY = "LIABILITY"
    TYPE_EQUITY = "EQUITY"
    TYPE_REVENUE = "REVENUE"
    TYPE_EXPENSE = "EXPENSE"
    # RESULT existe porque a DRE IMPRIME seus subtotais ("Lucro Líquido do
    # Exercício: 1.234,56"). Não são receita nem despesa, e jogá-los fora
    # descartaria a melhor conferência disponível: total impresso contra total
    # calculado a partir das folhas. checks_service exclui RESULT de toda soma
    # e o usa apenas como valor de conferência.
    TYPE_RESULT = "RESULT"
    TYPE_CHOICES = [
        (TYPE_ASSET, "Asset"),
        (TYPE_LIABILITY, "Liability"),
        (TYPE_EQUITY, "Equity"),
        (TYPE_REVENUE, "Revenue"),
        (TYPE_EXPENSE, "Expense"),
        (TYPE_RESULT, "Result"),
    ]

    ORIGIN_STANDARD = "STANDARD"
    ORIGIN_CUSTOM = "CUSTOM"
    ORIGIN_CHOICES = [
        (ORIGIN_STANDARD, "Standard"),
        (ORIGIN_CUSTOM, "Custom"),
    ]

    STATEMENT_BALANCE_SHEET = "BALANCE_SHEET"
    STATEMENT_INCOME_STATEMENT = "INCOME_STATEMENT"
    STATEMENT_CHOICES = [
        (STATEMENT_BALANCE_SHEET, "Balance Sheet"),
        (STATEMENT_INCOME_STATEMENT, "Income Statement"),
    ]

    account_code = models.CharField(
        max_length=30, primary_key=True, db_column="ACCOUNT_CODE"
    )
    account_name = models.CharField(max_length=255, db_column="ACCOUNT_NAME")
    account_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, db_column="ACCOUNT_TYPE"
    )
    statement = models.CharField(
        max_length=20, choices=STATEMENT_CHOICES, db_column="STATEMENT"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
        db_column="PARENT_CODE",
    )
    level = models.PositiveSmallIntegerField(default=0, db_column="LEVEL")
    display_order = models.PositiveIntegerField(default=0, db_column="DISPLAY_ORDER")
    origin = models.CharField(
        max_length=20,
        choices=ORIGIN_CHOICES,
        default=ORIGIN_CUSTOM,
        db_column="ORIGIN",
    )

    class Meta:
        db_table = "FINANCIALS_ACCOUNT_CHART"
        managed = True
        ordering = ["statement", "display_order", "account_code"]
        verbose_name = "Account Chart Entry"
        verbose_name_plural = "Account Chart"

    def __str__(self):
        return f"{self.account_code} — {self.account_name}"
