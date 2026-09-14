#!/usr/bin/env python
"""Django's command-line utility."""
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # `src/` no sys.path: os apps são importados como `credit.financials...`,
    # exatamente como no priv-data-home-app. NÃO mude isso — é o que faz a
    # migração ser um copiar de pastas.
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
