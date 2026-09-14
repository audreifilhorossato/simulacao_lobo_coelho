from credit.financials.models import AccountChart
from credit.financials.serializers.mixins import UpperCaseKeysMixin
from rest_framework import serializers


class AccountChartSerializer(UpperCaseKeysMixin, serializers.ModelSerializer):
    """Leitura do plano de contas.

    ``account_type``, ``statement``, ``level`` e ``parent`` são somente-leitura
    de propósito: quem os define é ``account_chart_service.derive`` a partir do
    ``account_code``. Deixá-los graváveis tornaria representável uma DESPESA
    pendurada no ATIVO.
    """

    class Meta:
        model = AccountChart
        fields = [
            "account_code",
            "account_name",
            "account_type",
            "statement",
            "parent",
            "level",
            "display_order",
            "origin",
        ]
        read_only_fields = [
            "account_type",
            "statement",
            "parent",
            "level",
            "display_order",
            "origin",
        ]
