"""Cadastro de empresa — a contraparte que envia as demonstrações.

PORTADO VERBATIM da plataforma Astecha. Não renomeie tabela nem coluna: a
migração depende de os nomes baterem exatamente.

PROJECT_ID / DEAL_ID são referências SOFT (texto, sem ForeignKey) para o
cadastro unificado da plataforma. Não transforme em ForeignKey: lá esses
cadastros vivem em outro alias de banco e o router bloqueia relação entre
aliases diferentes.
"""

from django.db import models


class Company(models.Model):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    ]

    id = models.BigAutoField(primary_key=True, db_column="COMPANY_ID")
    name = models.CharField(max_length=255, db_column="NAME")
    cnpj = models.CharField(max_length=18, unique=True, db_column="CNPJ")
    project_id = models.CharField(
        max_length=200, null=True, blank=True, db_column="PROJECT_ID"
    )
    deal_id = models.CharField(
        max_length=200, null=True, blank=True, db_column="DEAL_ID"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_column="STATUS"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="CREATED_AT")
    updated_at = models.DateTimeField(auto_now=True, db_column="UPDATED_AT")

    class Meta:
        db_table = "FINANCIALS_COMPANY"
        managed = True
        ordering = ["name"]
        verbose_name = "Financials Company"
        verbose_name_plural = "Financials Companies"

    def __str__(self):
        return f"{self.name} ({self.cnpj})"
