FROM python:3.12-slim

# tesseract + poppler: necessarios para OCR de PDF escaneado (Sprint 1).
# Se voce decidir nao fazer OCR, pode remover — mas ai metade da massa de
# dados fica fora do alcance e o criterio de acuracia sofre.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-por poppler-utils \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[parsing,dev]"

COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
