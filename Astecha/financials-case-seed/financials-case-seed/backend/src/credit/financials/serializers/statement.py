from credit.financials.models import FinancialStatement, FinancialStatementLine
from credit.financials.serializers.mixins import UpperCaseKeysMixin
from rest_framework import serializers


class FinancialStatementLineSerializer(UpperCaseKeysMixin, serializers.ModelSerializer):
    class Meta:
        model = FinancialStatementLine
        fields = ["id", "account", "raw_label", "value", "notes"]
        read_only_fields = fields


class FinancialStatementSerializer(UpperCaseKeysMixin, serializers.ModelSerializer):
    lines = FinancialStatementLineSerializer(many=True, read_only=True)

    class Meta:
        model = FinancialStatement
        fields = [
            "id",
            "company",
            "source_document",
            "statement_type",
            "period_end_date",
            "period_type",
            "currency",
            "status",
            "created_at",
            "extracted_by",
            "lines",
        ]
        read_only_fields = fields


# ── Escrita em lote ──────────────────────────────────────────────────────────
# O formato abaixo e o CONTRATO com o statement_service. Quando o analista
# aprova um rascunho, e este payload que o seu codigo monta.


class _StatementLineInput(serializers.Serializer):
    account_code = serializers.CharField(max_length=30)
    raw_label = serializers.CharField(max_length=500)
    value = serializers.DecimalField(max_digits=20, decimal_places=2)
    notes = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class _StatementInput(serializers.Serializer):
    statement_type = serializers.ChoiceField(
        choices=[c[0] for c in FinancialStatement.TYPE_CHOICES]
    )
    period_end_date = serializers.DateField()
    period_type = serializers.ChoiceField(
        choices=[c[0] for c in FinancialStatement.PERIOD_CHOICES]
    )
    currency = serializers.CharField(max_length=3, required=False, default="BRL")
    source_document_id = serializers.IntegerField(required=False, allow_null=True)
    overwrite = serializers.BooleanField(required=False, default=False)
    lines = _StatementLineInput(many=True)


class StatementWriteSerializer(serializers.Serializer):
    """Corpo de ``POST /statements/write`` e de ``POST /statements/validate``.

    Aceita chave em MAIUSCULA ou minuscula, como o resto da API.
    """

    company_id = serializers.IntegerField()
    statements = _StatementInput(many=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = {str(k).lower(): v for k, v in data.items()}
            for stmt in data.get("statements") or []:
                if not isinstance(stmt, dict):
                    continue
                for key in list(stmt):
                    if key != key.lower():
                        stmt[key.lower()] = stmt.pop(key)
                for line in stmt.get("lines") or []:
                    if not isinstance(line, dict):
                        continue
                    for key in list(line):
                        if key != key.lower():
                            line[key.lower()] = line.pop(key)
        return super().to_internal_value(data)
