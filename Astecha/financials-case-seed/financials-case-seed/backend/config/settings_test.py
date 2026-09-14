"""Perfil de testes: banco Postgres de teste + caches em memória (hermético)."""

from config.settings import *  # noqa: F401,F403

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-local",
    },
    # LocMem também no `shared` para o teste não precisar de Redis. Lembre que
    # em produção ele É Redis — um teste que dependa de o lock NÃO cruzar
    # processo está testando a coisa errada.
    "shared": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-shared",
    },
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
