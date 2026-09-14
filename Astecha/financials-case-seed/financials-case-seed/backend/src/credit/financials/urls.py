"""Roteamento — router do DRF para o app credit/financials.

``trailing_slash=False`` é deliberado, não descuido, e está assim na plataforma.
Trocar pelo ``DefaultRouter()` padrão já foi tentado e revertido: o
``APPEND_SLASH`` do Django só reescreve a URL para a requisição SEGUINTE, via
301 — então quem manda POST/PATCH/DELETE sem a barra recebe um redirect com o
CORPO DESCARTADO em vez de uma resposta. O sintoma é um teste que esperava 405
receber 301, e uma escrita que "sumiu" sem erro.

Em troca, a forma COM barra dá 404 aqui. Aceitável: nada chama assim.
"""

from credit.financials.views import (
    AccountChartViewSet,
    CompanyViewSet,
    FinancialStatementViewSet,
    SourceDocumentViewSet,
)
from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register(r"companies", CompanyViewSet, basename="financials-company")
router.register(
    r"account-chart", AccountChartViewSet, basename="financials-account-chart"
)
router.register(
    r"documents", SourceDocumentViewSet, basename="financials-source-document"
)
router.register(
    r"statements", FinancialStatementViewSet, basename="financials-statement"
)

# TODO (Sprint 2/3/4) — registre aqui, mantendo o mesmo prefixo:
#   router.register(r"extractions",    ExtractionViewSet,    basename="financials-extraction")
#   router.register(r"indicators",     IndicatorViewSet,     basename="financials-indicator")
#   router.register(r"covenant-rules", CovenantRuleViewSet,  basename="financials-covenant-rule")

urlpatterns = [
    re_path(r"^", include(router.urls)),
]
