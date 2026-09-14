from credit.financials.models import SourceDocument
from credit.financials.serializers.mixins import UpperCaseKeysMixin
from rest_framework import serializers


class SourceDocumentSerializer(UpperCaseKeysMixin, serializers.ModelSerializer):
    class Meta:
        model = SourceDocument
        fields = [
            "id",
            "company",
            "stage_path",
            "original_filename",
            "file_type",
            "upload_date",
            "processing_status",
        ]
        # PARSED_TEXT fica FORA da listagem de propósito: é um TextField que
        # pode ter centenas de KB e listar 50 documentos traria megabytes que
        # ninguem le. Exponha-o num endpoint de detalhe proprio se precisar.
        read_only_fields = fields


class SourceDocumentUploadSerializer(serializers.Serializer):
    """Entrada de ``POST /documents/upload`` (multipart).

    ``year``/``month`` definem a pasta de destino
    (``{COMPANY_ID}/{YYYY}/{MM}/``) e são a COMPETÊNCIA do documento, não a
    data de hoje: um balanço de 31/12/2025 enviado em março de 2026 vai para
    ``2025/12``. Errar isso espalha o acervo em pastas que ninguém acha depois.
    """

    company_id = serializers.IntegerField()
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    file = serializers.FileField()

    #: Limite de tamanho. Um PDF escaneado de 40 páginas fica em poucos MB;
    #: acima disso é quase sempre engano, e o custo de um LLM sobre isso não é.
    MAX_BYTES = 25 * 1024 * 1024
    ALLOWED_SUFFIXES = {".pdf": "PDF", ".xlsx": "XLSX", ".xls": "XLSX"}

    def validate_file(self, value):
        if value.size > self.MAX_BYTES:
            raise serializers.ValidationError(
                f"Arquivo tem {value.size} bytes; o limite e {self.MAX_BYTES}."
            )
        name = str(value.name or "").lower()
        if not any(name.endswith(sfx) for sfx in self.ALLOWED_SUFFIXES):
            raise serializers.ValidationError(
                "Formato nao suportado. Aceitos: "
                f"{', '.join(sorted(self.ALLOWED_SUFFIXES))}."
            )
        return value

    def file_type(self) -> str:
        name = str(self.validated_data["file"].name or "").lower()
        for sfx, kind in self.ALLOWED_SUFFIXES.items():
            if name.endswith(sfx):
                return kind
        raise serializers.ValidationError("Formato nao suportado.")
