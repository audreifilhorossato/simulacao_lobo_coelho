"""Paginação padrão — envelope ``{count, next, previous, results}``.

Espelha ``StandardPagination`` da plataforma. Não troque por
``LimitOffsetPagination`` nem invente um envelope próprio: o frontend da
Astecha lê exatamente estas quatro chaves.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500
