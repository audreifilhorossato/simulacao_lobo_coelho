from credit.financials.models import Company
from credit.financials.serializers import CompanySerializer
from credit.financials.views.pagination import StandardPagination
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets


@extend_schema(tags=["Credit / Financials"])
class CompanyViewSet(viewsets.ModelViewSet):
    """Cadastro de empresas."""

    serializer_class = CompanySerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Company.objects.all()
        if status_f := self.request.query_params.get("status"):
            qs = qs.filter(status=status_f)
        if search := self.request.query_params.get("search"):
            # `icontains`, nao `ILIKE` cru: o ORM traduz para o dialeto certo em
            # Postgres E em Snowflake. Regra R5.
            qs = qs.filter(name__icontains=search)
        return qs.order_by("name")

    @extend_schema(
        parameters=[
            OpenApiParameter("status", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("search", str, OpenApiParameter.QUERY, required=False),
        ],
        summary="Lista empresas (filtros: status, search)",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
