"""Montagem das rotas.

O prefixo é `api/v1/credit/financials/` — DOIS segmentos de domínio
(`credit` + `financials`), exatamente como no priv-data-home-app. Montagem rasa
(`api/v1/financials/`) é rejeitada por teste lá; não invente um caminho novo.
"""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/v1/credit/financials/", include("credit.financials.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
