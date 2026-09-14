"""Erros de dominio que a camada HTTP sabe traduzir.

ValueError    -> 400 (payload invalido)
LookupError   -> 404 (nao existe)
ConflictError -> 409 (existe, mas o estado atual proibe a operacao)

O mapeamento vive em views/_helpers.py. Nao levante HttpResponse de dentro de
um service: service nao conhece HTTP (regra R4).
"""


class ConflictError(Exception):
    """A operacao e valida, mas conflita com o estado atual do recurso."""
