"""Balanço / DRE padronizados, extraídos de um SourceDocument.

PORTADO VERBATIM da plataforma Astecha.

FinancialStatementLine.raw_label guarda o rótulo EXATAMENTE como apareceu no
documento (auditoria e rastreabilidade) ao lado da conta padronizada em que ele
foi mapeado. Nunca descarte o raw_label: sem ele ninguém consegue conferir o
de-para, e é ele que alimenta o aprendizado do mapeamento.
"""

from credit.financials.models.account_chart import AccountChart
from credit.financials.models.company import Company
from credit.financials.models.source_document import SourceDocument
from django.db import models


class FinancialStatement(models.Model):
    TYPE_BALANCE_SHEET = "BALANCE_SHEET"
    TYPE_INCOME_STATEMENT = "INCOME_STATEMENT"
    TYPE_CHOICES = [
        (TYPE_BALANCE_SHEET, "Balance Sheet"),
        (TYPE_INCOME_STATEMENT, "Income Statement"),
    ]

    PERIOD_MONTHLY = "MONTHLY"
    PERIOD_QUARTERLY = "QUARTERLY"
    PERIOD_ANNUAL = "ANNUAL"
    PERIOD_CHOICES = [
        (PERIOD_MONTHLY, "Monthly"),
        (PERIOD_QUARTERLY, "Quarterly"),
        (PERIOD_ANNUAL, "Annual"),
    ]

    STATUS_DRAFT = "DRAFT"
    STATUS_FINAL = "FINAL"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_FINAL, "Final"),
    ]

    id = models.BigAutoField(primary_key=True, db_column="STATEMENT_ID")
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="statements",
        db_column="COMPANY_ID",
    )
    source_document = models.ForeignKey(
        SourceDocument,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="statements",
        db_column="SOURCE_DOCUMENT_ID",
    )
    statement_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, db_column="STATEMENT_TYPE"
    )
    period_end_date = models.DateField(db_column="PERIOD_END_DATE")
    period_type = models.CharField(
        max_length=20, choices=PERIOD_CHOICES, db_column="PERIOD_TYPE"
    )
    currency = models.CharField(max_length=3, default="BRL", db_column="CURRENCY")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_column="STATUS"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="CREATED_AT")
    extracted_by = models.CharField(
        max_length=100, null=True, blank=True, db_column="EXTRACTED_BY"
    )

    class Meta:
        db_table = "FINANCIALS_STATEMENT"
        managed = True
        ordering = ["-period_end_date"]
        # ATENCAO: no Snowflake esta restricao NAO e imposta pelo banco. Ela e a
        # CHAVE NATURAL do registro, e quem a garante e o statement_service
        # (lock no Redis + validacao em codigo). Nao escreva nada que confie no
        # banco para barrar duplicata. Ver regra R6 do anexo tecnico.
        unique_together = [("company", "statement_type", "period_end_date")]
        verbose_name = "Financial Statement"
        verbose_name_plural = "Financial Statements"

    def __str__(self):
        return f"{self.company_id} {self.statement_type} {self.period_end_date}"


class FinancialStatementLine(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="LINE_ID")
    statement = models.ForeignKey(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name="lines",
        db_column="STATEMENT_ID",
    )
    account = models.ForeignKey(
        AccountChart,
        on_delete=models.PROTECT,
        related_name="statement_lines",
        db_column="ACCOUNT_CODE",
    )
    raw_label = models.CharField(max_length=500, db_column="RAW_LABEL")
    value = models.DecimalField(max_digits=20, decimal_places=2, db_column="VALUE")
    notes = models.TextField(null=True, blank=True, db_column="NOTES")

    class Meta:
        db_table = "FINANCIALS_STATEMENT_LINE"
        managed = True
        ordering = ["id"]
        verbose_name = "Financial Statement Line"
        verbose_name_plural = "Financial Statement Lines"

    def __str__(self):
        return f"{self.raw_label} = {self.value}"
