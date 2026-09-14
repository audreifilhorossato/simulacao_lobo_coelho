"""Armazenamento do arquivo bruto — A COSTURA DE MIGRAÇÃO Nº 1.

Aqui a implementação grava no sistema de arquivos local. Na Astecha, as mesmas
quatro funções gravam num *stage* interno do Snowflake, via comandos
``PUT`` / ``GET`` / ``LIST`` / ``REMOVE``.

**As assinaturas abaixo são idênticas às do ``stage_service.py`` da plataforma,
função por função e argumento por argumento.** É por isso que trocar um pelo
outro é substituir UM arquivo. Se você mudar uma assinatura, quebra a migração
— e o corretor vai reparar.

Layout de caminho (também idêntico): ``{COMPANY_ID}/{YYYY}/{MM}/{arquivo}``.
Guarde no banco o caminho RELATIVO devolvido por ``put_file`` (é o que vai em
``SourceDocument.stage_path``), nunca um caminho absoluto do seu disco — um
caminho absoluto local não significa nada dentro do Snowflake.

REGRAS
------
- Nenhum outro módulo pode abrir arquivo direto. Todo acesso passa por aqui.
- Nada de ``pathlib`` vazando para fora deste módulo: o Snowflake não tem
  ``Path``.
- ``put_file`` sobrescreve por padrão (``OVERWRITE=TRUE`` no lado Snowflake).
"""

from __future__ import annotations

import logging
import os
import re
import shutil

from django.conf import settings

logger = logging.getLogger(__name__)

STAGE = "FINANCIALS_UPLOADS"

_COMPANY_RE = re.compile(r"^[A-Z0-9_]+$")


def _root() -> str:
    root = settings.FINANCIALS_STORAGE_ROOT
    os.makedirs(root, exist_ok=True)
    return root


def sanitize_filename(name: str) -> str:
    """Mantém um nome-base legível e seguro (sem separador de caminho nem
    aspas). Porta de entrada contra *path traversal*: um upload chamado
    ``../../etc/passwd`` vira ``passwd``."""
    base = os.path.basename(str(name or "").replace("\\", "/"))
    base = re.sub(r"[^A-Za-z0-9._\- ]+", "_", base).strip()
    return base or "upload.pdf"


def folder_path(company_id, year: int, month: int) -> str:
    """Subcaminho de ``(company_id, year, month)``: ``{COMPANY_ID}/{YYYY}/{MM}``."""
    company = str(company_id).strip().upper()
    if not _COMPANY_RE.match(company):
        raise ValueError(f"Invalid company_id: {company_id!r}")
    year, month = int(year), int(month)
    if not (2000 <= year <= 2100 and 1 <= month <= 12):
        raise ValueError(f"Invalid year/month: {year}-{month}")
    return f"{company}/{year:04d}/{month:02d}"


def _safe_object_name(file_name: str) -> str:
    safe = sanitize_filename(file_name)
    if not safe or set(safe) <= {"."}:
        raise ValueError(f"Invalid file name: {file_name!r}")
    return safe


def put_file(
    file_bytes: bytes, company_id, year: int, month: int, file_name: str
) -> str:
    """Grava ``file_bytes`` em ``{COMPANY_ID}/{YYYY}/{MM}/{file_name}`` e
    devolve o caminho RELATIVO (é ele que vai para ``SourceDocument.stage_path``).
    """
    rel_dir = folder_path(company_id, year, month)
    filename = sanitize_filename(file_name)
    abs_dir = os.path.join(_root(), *rel_dir.split("/"))
    os.makedirs(abs_dir, exist_ok=True)
    with open(os.path.join(abs_dir, filename), "wb") as fh:
        fh.write(file_bytes)

    rel = f"{rel_dir}/{filename}"
    logger.info("Financials upload gravado em %s/%s", STAGE, rel)
    return rel


def get_file(company_id, year: int, month: int, file_name: str) -> bytes:
    """Lê um arquivo gravado e devolve os bytes crus."""
    rel_dir = folder_path(company_id, year, month)
    safe = _safe_object_name(file_name)
    path = os.path.join(_root(), *rel_dir.split("/"), safe)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Stage file not found: {rel_dir}/{safe}")
    with open(path, "rb") as fh:
        return fh.read()


def list_files(company_id, year: int, month: int) -> list[dict]:
    """``[{file_name, relative_path, size, last_modified}]``.

    Devolve ``[]`` quando a pasta ainda não existe — ausência não é erro (o
    ``LIST`` do Snowflake se comporta igual)."""
    rel_dir = folder_path(company_id, year, month)
    abs_dir = os.path.join(_root(), *rel_dir.split("/"))
    if not os.path.isdir(abs_dir):
        return []

    files: list[dict] = []
    for base in os.listdir(abs_dir):
        if base.startswith("."):
            continue
        full = os.path.join(abs_dir, base)
        if not os.path.isfile(full):
            continue
        stat = os.stat(full)
        files.append(
            {
                "file_name": base,
                "relative_path": f"{rel_dir}/{base}",
                "size": stat.st_size,
                "last_modified": str(int(stat.st_mtime)),
            }
        )
    files.sort(key=lambda f: f["file_name"].lower())
    return files


def remove_file(company_id, year: int, month: int, file_name: str) -> str:
    """Apaga um arquivo. Devolve o caminho relativo removido."""
    rel_dir = folder_path(company_id, year, month)
    safe = _safe_object_name(file_name)
    path = os.path.join(_root(), *rel_dir.split("/"), safe)
    if os.path.exists(path):
        os.remove(path)
    logger.info("Financials arquivo removido: %s/%s", STAGE, f"{rel_dir}/{safe}")
    return f"{rel_dir}/{safe}"


def purge_all() -> None:
    """SÓ PARA TESTE — apaga a raiz inteira. Nunca chame em código de produção;
    o equivalente no Snowflake seria um ``REMOVE`` no stage todo."""
    root = settings.FINANCIALS_STORAGE_ROOT
    shutil.rmtree(root, ignore_errors=True)
