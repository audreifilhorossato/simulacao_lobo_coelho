from django.apps import AppConfig


class FinancialsConfig(AppConfig):
    # `name` e o caminho de import; `label` e global e imutavel na pratica --
    # e ele que aparece em DJANGO_MIGRATIONS. Nao renomeie.
    name = "credit.financials"
    label = "financials"
    verbose_name = "Credit / Financials"
