"""Configuração do backend do case Financials.

Postgres aqui, Snowflake na Astecha. As diferenças entre os dois estão isoladas
NESTE arquivo — é por isso que o resto do código não pode usar nada específico
de Postgres (regra R5 do anexo técnico).
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-nao-use-em-producao")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "credit.financials",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "financials"),
        "USER": os.environ.get("POSTGRES_USER", "financials"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "financials"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# Na Astecha existem vários aliases (credit, controller, ...). Aqui há um só.
# O código NUNCA deve escrever `using="default"` cru: use a constante.
FINANCIALS_DB_ALIAS = "default"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_TZ = True
USE_I18N = False

STATIC_URL = "static/"

REST_FRAMEWORK = {
    # A plataforma controla auth na borda (SPCS). Aqui fica aberto de propósito —
    # NÃO construa autenticação (anti-requisito do case).
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Financials API — Insper Code Jr. 2026.2",
    "DESCRIPTION": "Extração e padronização de demonstrações financeiras.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Cache ────────────────────────────────────────────────────────────────────
# DOIS aliases, espelhando a plataforma:
#   default -> memória do processo (memoização barata, pode ficar stale)
#   shared  -> Redis (ÚNICO lugar correto para estado que cruza processo:
#              lock entre web e worker, invalidação, metadados de job)
# Ver regra R6: Snowflake não impõe UNIQUE nem FK e não tem row lock, então o
# lock de escrita mora no Redis, não no banco.
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "financials-local",
    },
    "shared": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_CACHE_URL", "redis://redis:6379/1"),
    },
}

# ── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 10 * 60

# ── Armazenamento de arquivo ─────────────────────────────────────────────────
# Aqui: sistema de arquivos local. Na Astecha: stage do Snowflake.
# A troca é UM arquivo (services/storage.py) porque a assinatura é a mesma.
FINANCIALS_STORAGE_ROOT = os.environ.get(
    "FINANCIALS_STORAGE_ROOT", str(BASE_DIR / "var" / "uploads")
)

# ── Provider de extração ─────────────────────────────────────────────────────
# Nome registrado em services/extraction/providers/__init__.py.
FINANCIALS_EXTRACTION_PROVIDER = os.environ.get(
    "FINANCIALS_EXTRACTION_PROVIDER", "rule_based"
)

CORS_ALLOW_ALL_ORIGINS = True
