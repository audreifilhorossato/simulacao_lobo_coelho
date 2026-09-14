from credit.financials.models import Company
from credit.financials.serializers.mixins import UpperCaseKeysMixin
from rest_framework import serializers


class CompanySerializer(UpperCaseKeysMixin, serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "cnpj",
            "project_id",
            "deal_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_cnpj(self, value):
        """Normaliza para 14 dígitos. NÃO valida o dígito verificador aqui —
        se você quiser essa validação (e ela é útil), coloque num service e
        cubra com teste: um CNPJ vindo de OCR erra dígito com frequência, e o
        comportamento certo é AVISAR, não recusar o cadastro."""
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if len(digits) != 14:
            raise serializers.ValidationError(
                f"CNPJ deve ter 14 digitos (recebido: {len(digits)})."
            )
        return digits
