from credit.financials.models import AccountChart
from credit.financials.serializers import AccountChartSerializer
from credit.financials.services import account_chart_service
from credit.financials.views._helpers import respond
from credit.financials.views.pagination import StandardPagination
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action


@extend_schema(tags=["Credit / Financials"])
class AccountChartViewSet(viewsets.ReadOnlyModelViewSet):
    """Plano de contas padronizado.

    Leitura livre. Escrita SÓ de conta CUSTOM, e passando pelo service (que
    deriva tipo/nível/pai do código e protege as linhas STANDARD).
    """

    serializer_class = AccountChartSerializer
    pagination_class = StandardPagination
    lookup_field = "account_code"
    # Códigos contêm ponto: sem isto o router corta '1.01.01' em '1'.
    lookup_value_regex = r"[^/]+"

    def get_queryset(self):
        qs = AccountChart.objects.all()
        if statement := self.request.query_params.get("statement"):
            qs = qs.filter(statement=statement)
        if origin := self.request.query_params.get("origin"):
            qs = qs.filter(origin=origin)
        if level := self.request.query_params.get("level"):
            qs = qs.filter(level=level)
        return qs.order_by("statement", "display_order", "account_code")

    @extend_schema(
        parameters=[
            OpenApiParameter("statement", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("origin", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("level", int, OpenApiParameter.QUERY, required=False),
        ],
        summary="Lista o plano de contas (filtros: statement, origin, level)",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Cria/atualiza contas CUSTOM em lote",
        request=None,
        responses=None,
    )
    @action(detail=False, methods=["post"], url_path="upsert")
    def upsert(self, request):
        entries = request.data if isinstance(request.data, list) else [request.data]
        return respond(account_chart_service.upsert_many, entries)
