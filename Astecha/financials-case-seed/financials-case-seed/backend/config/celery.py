"""Celery — o ÚNICO mecanismo assíncrono permitido (regra R7).

Nada de threading, BackgroundTasks ou asyncio.create_task: a plataforma roda em
vários processos e um job que vive na memória de um deles não existe para os
outros.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("financials")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["credit.financials"])
