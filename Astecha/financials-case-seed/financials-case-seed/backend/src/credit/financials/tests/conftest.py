"""Fixtures compartilhadas dos testes de financials."""

from datetime import date
from decimal import Decimal

import pytest
from credit.financials.models import Company, FinancialStatement
from rest_framework.test import APIClient


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def company(db):
    return Company.objects.create(name="Empresa Exemplo SA", cnpj="12345678000199")


@pytest.fixture
def balanco_valido():
    """Um balanco que FECHA: Ativo (1000) = Passivo (600) + PL (400).

    Repare que so ha FOLHAS aqui. Se voce acrescentar o pai '1.01' junto com os
    filhos, o checks_service passa a usar o pai como conferencia — que e o
    comportamento certo, e um bom teste a escrever.
    """
    return {
        "company_id": None,  # preenchido pelo teste
        "statements": [
            {
                "statement_type": FinancialStatement.TYPE_BALANCE_SHEET,
                "period_end_date": str(date(2025, 12, 31)),
                "period_type": FinancialStatement.PERIOD_ANNUAL,
                "lines": [
                    {
                        "account_code": "1.01.01",
                        "raw_label": "Caixa e equivalentes",
                        "value": str(Decimal("1000.00")),
                    },
                    {
                        "account_code": "2.01.01",
                        "raw_label": "Fornecedores",
                        "value": str(Decimal("600.00")),
                    },
                    {
                        "account_code": "3.01",
                        "raw_label": "Capital social",
                        "value": str(Decimal("400.00")),
                    },
                ],
            }
        ],
    }
