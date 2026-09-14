"""Documentos brutos.

O que está aqui: listar e fazer upload.
O que VOCÊS acrescentam: ``POST /documents/{id}/extract`` (202 + task_id) e o
endpoint de polling. Ver o TODO no fim do arquivo e ``tasks.py``.
"""

from credit.financials.models import Company, SourceDocument
from credit.financials.serializers import (
    SourceDocumentSerializer,
    SourceDocumentUploadSerializer,
)
from credit.financials.services import storage
from credit.financials.views.pagination import StandardPagination
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response


@extend_schema(tags=["Credit / Financials"])
class SourceDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """Documentos brutos (balanço/DRE) enviados por empresa, com status de parsing."""

    serializer_class = SourceDocumentSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = SourceDocument.objects.all()
        if company_id := self.request.query_params.get("company_id"):
            qs = qs.filter(company_id=company_id)
        if status_f := self.request.query_params.get("status"):
            qs = qs.filter(processing_status=status_f)
        return qs.order_by("-upload_date")

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", int, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("status", str, OpenApiParameter.QUERY, required=False),
        ],
        summary="Lista documentos (filtros: company_id, status)",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Envia um PDF/XLSX bruto e registra o documento",
        request=SourceDocumentUploadSerializer,
        responses={201: SourceDocumentSerializer},
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="upload",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload(self, request):
        serializer = SourceDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not Company.objects.filter(pk=data["company_id"]).exists():
            return Response(
                {"detail": f"Company {data['company_id']} nao existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload = data["file"]
        stage_path = storage.put_file(
            upload.read(),
            data["company_id"],
            data["year"],
            data["month"],
            upload.name,
        )

        # O caminho e unico por construcao (empresa/ano/mes/nome). Reenviar o
        # mesmo arquivo SUBSTITUI o binario e reaproveita o registro, em vez de
        # criar um segundo documento apontando para o mesmo lugar — o que
        # violaria o unique de STAGE_PATH e, pior, faria a metrica contar o
        # mesmo documento duas vezes.
        document, created = SourceDocument.objects.update_or_create(
            stage_path=stage_path,
            defaults={
                "company_id": data["company_id"],
                "original_filename": upload.name,
                "file_type": serializer.file_type(),
                "processing_status": SourceDocument.STATUS_PENDING,
                "parsed_text": None,
            },
        )
        return Response(
            SourceDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    # ── TODO (Sprint 1/2) ────────────────────────────────────────────────────
    # @action(detail=True, methods=["post"], url_path="extract")
    # def extract(self, request, pk=None):
    #     """Enfileira a extracao. DEVE devolver 202 + {"task_id", "extraction_id"}.
    #
    #     NAO faca o parse aqui dentro. Um PDF escaneado de 40 paginas com OCR
    #     leva minutos: a requisicao estoura o timeout do gunicorn, o usuario ve
    #     502 e o trabalho e perdido no meio. Enfileire em Celery (regra R7).
    #     """
