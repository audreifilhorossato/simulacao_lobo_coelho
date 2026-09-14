"""Tradução de erro de domínio para HTTP, num lugar só.

Os services levantam exceção de DOMÍNIO (``ValueError``, ``LookupError``,
``ConflictError``) e não sabem o que é um status HTTP — é o que mantém a regra
R4 verdadeira. Quem traduz é ``respond``.

A mensagem de erro tem que ser AUTOSSUFICIENTE numa string só: quem consome a
API pode ser um agente, e o corpo aninhado que você acha bonito costuma ser
descartado no caminho. Escreva a mensagem que você gostaria de ler às duas da
manhã.
"""

from credit.financials.services.errors import ConflictError
from rest_framework import status
from rest_framework.response import Response


def respond(fn, *args, ok_status=status.HTTP_200_OK, **kwargs) -> Response:
    """Executa ``fn(*args, **kwargs)`` e embrulha o resultado numa Response.

        ValueError    -> 400
        LookupError   -> 404
        ConflictError -> 409

    Qualquer outra exceção sobe: 500 é a resposta certa para um defeito que
    você não previu, e engoli-la aqui esconderia o bug do Sentry.
    """
    try:
        return Response(fn(*args, **kwargs), status=ok_status)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except LookupError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    except ConflictError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)


def execution_user(request) -> str:
    """Quem está escrevendo. Vai para ``FinancialStatement.EXTRACTED_BY``.

    Na plataforma vem do usuário autenticado. Aqui não há autenticação (é
    anti-requisito construir uma), então aceitamos o cabeçalho ``X-User`` e
    caímos num default. Não invente login por causa disto.
    """
    return str(request.headers.get("X-User") or "insper-code").strip()[:100]
