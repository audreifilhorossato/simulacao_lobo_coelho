from credit.financials.models import FinancialStatement
from credit.financials.serializers import (
    FinancialStatementSerializer,
    StatementWriteSerializer,
)
from credit.financials.services import checks_service, statement_service
from credit.financials.views._helpers import execution_user, respond
from credit.financials.views.pagination import StandardPagination
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


@extend_schema(tags=["Credit / Financials"])
class FinancialStatementViewSet(viewsets.ReadOnlyModelViewSet):
    """Demonstrações padronizadas.

    A escrita não é `POST /statements`: é `POST /statements/write`, em LOTE e
    atômica. Isso é deliberado — um balanço e a DRE do mesmo período têm que
    entrar juntos ou não entrar, e um reenvio depois de timeout tem que
    convergir em vez de duplicar.
    """

    serializer_class = FinancialStatementSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = FinancialStatement.objects.all().prefetch_related("lines")
        params = self.request.query_params
        if company_id := params.get("company_id"):
            qs = qs.filter(company_id=company_id)
        if statement_type := params.get("statement_type"):
            qs = qs.filter(statement_type=statement_type)
        if status_f := params.get("status"):
            qs = qs.filter(status=status_f)
        if period_from := params.get("period_from"):
            qs = qs.filter(period_end_date__gte=period_from)
        if period_to := params.get("period_to"):
            qs = qs.filter(period_end_date__lte=period_to)
        return qs.order_by("-period_end_date", "statement_type")

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", int, OpenApiParameter.QUERY, required=False),
            OpenApiParameter(
                "statement_type", str, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter("status", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter(
                "period_from", str, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter("period_to", str, OpenApiParameter.QUERY, required=False),
        ],
        summary="Lista demonstracoes",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Valida o payload sem escrever nada (diagnostico)",
        request=StatementWriteSerializer,
    )
    @action(detail=False, methods=["post"], url_path="validate")
    def validate_payload(self, request):
        serializer = StatementWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return respond(statement_service.validate_statements, serializer.validated_data)

    @extend_schema(
        summary="Escreve demonstracoes + linhas em lote (atomico)",
        request=StatementWriteSerializer,
    )
    @action(detail=False, methods=["post"], url_path="write")
    def write(self, request):
        serializer = StatementWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return respond(
            statement_service.write_statements,
            serializer.validated_data,
            execution_user=execution_user(request),
        )

    @extend_schema(summary="Conferencias contabeis de uma demonstracao")
    @action(detail=True, methods=["get"], url_path="checks")
    def checks(self, request, pk=None):
        statement = (
            FinancialStatement.objects.filter(pk=pk)
            .prefetch_related("lines__account")
            .first()
        )
        if statement is None:
            return Response(
                {"detail": f"Demonstracao {pk} nao existe."},
                status=status.HTTP_404_NOT_FOUND,
            )
        lines = [
            {"account": line.account, "value": line.value, "raw_label": line.raw_label}
            for line in statement.lines.all()
        ]
        return Response(
            {
                "statement_id": statement.id,
                "checks": checks_service.run_checks(statement.statement_type, lines),
            }
        )

    @extend_schema(summary="Exclui uma demonstracao DRAFT")
    def destroy(self, request, pk=None):
        return respond(statement_service.delete_statement, pk)

    # ReadOnlyModelViewSet nao registra DELETE; declaramos a acao explicitamente
    # para manter o verbo REST sem abrir POST/PUT genericos (a escrita e so pelo
    # /write, que e atomico e em lote).
    http_method_names = ["get", "post", "delete", "head", "options"]
