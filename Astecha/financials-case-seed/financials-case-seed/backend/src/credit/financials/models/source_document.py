"""Documento bruto (balanço/DRE) enviado por empresa.

PORTADO VERBATIM da plataforma Astecha.

STAGE_PATH aponta para o arquivo no armazenamento (`services/storage.py`);
PARSED_TEXT guarda o texto/tabelas normalizados depois que a task assíncrona de
parse termina.

Uma coluna de FATOR DE ESCALA (o "Em R$ mil" do cabeçalho) NÃO existe aqui de
propósito — é uma das que vocês vão precisar acrescentar. Antes de sair
escrevendo, decidam: o fator vale para o documento inteiro, ou pode variar
entre o balanço e a DRE dentro do mesmo PDF?
"""

from credit.financials.models.company import Company
from django.db import models


class SourceDocument(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PARSING = "PARSING"
    STATUS_PARSED = "PARSED"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PARSING, "Parsing"),
        (STATUS_PARSED, "Parsed"),
        (STATUS_FAILED, "Failed"),
    ]

    FILE_TYPE_PDF = "PDF"
    FILE_TYPE_XLSX = "XLSX"
    FILE_TYPE_CHOICES = [
        (FILE_TYPE_PDF, "PDF"),
        (FILE_TYPE_XLSX, "XLSX"),
    ]

    id = models.BigAutoField(primary_key=True, db_column="DOCUMENT_ID")
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="source_documents",
        db_column="COMPANY_ID",
    )
    stage_path = models.CharField(max_length=1000, unique=True, db_column="STAGE_PATH")
    original_filename = models.CharField(max_length=500, db_column="ORIGINAL_FILENAME")
    file_type = models.CharField(
        max_length=10, choices=FILE_TYPE_CHOICES, db_column="FILE_TYPE"
    )
    upload_date = models.DateTimeField(auto_now_add=True, db_column="UPLOAD_DATE")
    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        db_column="PROCESSING_STATUS",
    )
    parsed_text = models.TextField(null=True, blank=True, db_column="PARSED_TEXT")

    class Meta:
        db_table = "FINANCIALS_SOURCE_DOCUMENT"
        managed = True
        ordering = ["-upload_date"]
        verbose_name = "Financials Source Document"
        verbose_name_plural = "Financials Source Documents"

    def __str__(self):
        return f"{self.original_filename} ({self.processing_status})"
