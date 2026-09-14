#!/usr/bin/env python
"""Arreio de avaliação da extração — o número que vale 30% da nota.

    python eval/run.py                      # provider do .env
    python eval/run.py --provider naive     # o piso: tira 0%
    python eval/run.py --provider rule_based
    python eval/run.py --markdown           # saida para o resumo do GitHub Actions
    python eval/run.py --case bp-duas-colunas   # so um caso, com detalhe

POR QUE ISTO EXISTE
-------------------
Sem uma medida, "melhorou" é opinião. Este script transforma a extração num
número comparável entre sprints e entre providers. Rode-o desde a Sprint 1,
com o ``naive``, e guarde o resultado: os três números (naive -> rule_based ->
llm) lado a lado SÃO a sua apresentação final.

COMO ELE FUNCIONA
-----------------
Cada caso em ``eval/cases/<slug>/`` tem dois arquivos:

  ``parsed.json``    — o documento JÁ PARSEADO (texto + tabelas). É a entrada do
                       provider. Vem pronto para que vocês possam medir a
                       extração antes de o parser existir.
  ``expected.json``  — o gabarito: o que uma extração perfeita produziria.

O que é medido, e por quê:

  DOC_OK        o provider devolveu o número certo de demonstrações. Um balanço
                com duas colunas de período são DUAS demonstrações; devolver
                uma só já está errado antes de olhar valor nenhum.
  PERIODO       a competência (``period_end_date``) bate. Errar aqui grava o
                balanço no ano errado, e ninguém percebe até a comparação
                histórica sair torta.
  ESCALA        o ``scale_factor`` bate. É o erro de 1000x: o mais barato de
                cometer e o mais caro de descobrir.
  CONTA_REC     recall do de-para: das linhas do gabarito, quantas o provider
                achou E mapeou na conta certa.
  CONTA_PREC    precisão: das linhas que o provider entregou, quantas estavam
                certas. Recall alto com precisão baixa = o provider está
                chutando conta, e o analista revisa tudo do mesmo jeito.
  VALOR         das linhas com conta certa, quantas têm o valor certo (com
                escala e sinal aplicados).
  SCORE         média ponderada. É o número que vai para a nota.

REGRA DE OURO
-------------
Não edite ``expected.json`` para o seu provider passar. O gabarito é o
documento; se ele estiver errado, abra uma issue e mostre o porquê — isso conta
a favor. Ajustar o gabarito para caber no código é a única forma de zerar o
critério inteiro.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
REPO_DIR = EVAL_DIR.parent
CASES_DIR = EVAL_DIR / "cases"

sys.path.insert(0, str(REPO_DIR / "backend" / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(REPO_DIR / "backend"))

#: Tolerância de valor. 0,01 absoluto cobre arredondamento de centavo; a parte
#: relativa cobre um documento em milhares em que o próprio papel arredondou.
_TOL_ABS = Decimal("0.01")
_TOL_REL = Decimal("0.0001")

#: Pesos do SCORE. Somam 1.0. Conta e valor pesam mais porque são o produto;
#: escala e período pesam porque um erro ali invalida o documento inteiro.
WEIGHTS = {
    "doc_ok": 0.10,
    "periodo": 0.15,
    "escala": 0.15,
    "conta_rec": 0.25,
    "conta_prec": 0.15,
    "valor": 0.20,
}


def _dec(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def _close(a: Decimal, b: Decimal) -> bool:
    return abs(a - b) <= max(_TOL_ABS, _TOL_REL * max(abs(a), abs(b)))


def _load_django():
    import django

    django.setup()


def _build_parsed_document(payload: dict):
    from credit.financials.services.extraction.types import ParsedDocument, ParsedTable

    return ParsedDocument(
        document_id=payload.get("document_id", 0),
        file_type=payload.get("file_type", "PDF"),
        text=payload.get("text", ""),
        page_count=payload.get("page_count", 0),
        tables=[
            ParsedTable(page=t.get("page", 1), rows=t.get("rows", []))
            for t in payload.get("tables", [])
        ],
    )


def _key(statement_type, period_end_date):
    return (str(statement_type), str(period_end_date))


def score_case(case_dir: Path, provider, verbose: bool = False) -> dict:
    parsed = json.loads((case_dir / "parsed.json").read_text(encoding="utf-8"))
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    document = _build_parsed_document(parsed)
    result = provider.extract(document)

    exp_stmts = expected["statements"]
    got_stmts = result.drafts

    got_by_key = {_key(d.statement_type, d.period_end_date): d for d in got_stmts}

    doc_ok = 1.0 if len(got_stmts) == len(exp_stmts) else 0.0

    periodo_hits = 0
    escala_hits = 0
    exp_lines_total = 0
    got_lines_total = 0
    conta_hits = 0
    valor_hits = 0
    misses: list[str] = []

    for exp in exp_stmts:
        k = _key(exp["statement_type"], exp["period_end_date"])
        got = got_by_key.get(k)
        exp_lines = exp["lines"]
        exp_lines_total += len(exp_lines)

        if got is None:
            misses.append(f"demonstracao ausente: {k[0]} {k[1]}")
            continue

        periodo_hits += 1
        if int(getattr(got, "scale_factor", 1) or 1) == int(exp.get("scale_factor", 1)):
            escala_hits += 1
        else:
            misses.append(
                f"escala {k[0]} {k[1]}: esperado {exp.get('scale_factor', 1)}, "
                f"veio {getattr(got, 'scale_factor', None)}"
            )

        got_by_code: dict[str, list] = {}
        for line in got.lines:
            got_lines_total += 1
            if line.account_code:
                got_by_code.setdefault(str(line.account_code), []).append(line)

        for exp_line in exp_lines:
            code = str(exp_line["account_code"])
            candidates = got_by_code.get(code)
            if not candidates:
                misses.append(f"conta nao mapeada: {code} ({exp_line['raw_label']})")
                continue
            conta_hits += 1

            exp_value = _dec(exp_line["value"])
            got_value = _dec(getattr(candidates[0], "value", None))
            if (
                got_value is not None
                and exp_value is not None
                and _close(got_value, exp_value)
            ):
                valor_hits += 1
            else:
                misses.append(
                    f"valor de {code}: esperado {exp_value}, veio {got_value}"
                )

    # Demonstrações a mais (o provider inventou uma competência que não existe)
    for k in got_by_key:
        if k not in {
            _key(e["statement_type"], e["period_end_date"]) for e in exp_stmts
        }:
            misses.append(f"demonstracao inventada: {k[0]} {k[1]}")

    n_stmts = max(len(exp_stmts), 1)
    metrics = {
        "doc_ok": doc_ok,
        "periodo": periodo_hits / n_stmts,
        "escala": escala_hits / n_stmts,
        "conta_rec": conta_hits / exp_lines_total if exp_lines_total else 0.0,
        "conta_prec": conta_hits / got_lines_total if got_lines_total else 0.0,
        "valor": valor_hits / conta_hits if conta_hits else 0.0,
    }
    metrics["score"] = sum(metrics[k] * w for k, w in WEIGHTS.items())

    if verbose:
        print(f"\n--- {case_dir.name} ---")
        for m in misses[:40]:
            print(f"  x {m}")
        if len(misses) > 40:
            print(f"  ... e mais {len(misses) - 40}")

    return {
        "case": case_dir.name,
        "warnings": list(result.warnings),
        **metrics,
    }


def _fmt_pct(value: float) -> str:
    return f"{value * 100:5.1f}%"


def render_table(rows: list[dict], provider_name: str, markdown: bool) -> str:
    cols = [
        ("case", "CASO"),
        ("doc_ok", "DOC_OK"),
        ("periodo", "PERIODO"),
        ("escala", "ESCALA"),
        ("conta_rec", "CONTA_REC"),
        ("conta_prec", "CONTA_PREC"),
        ("valor", "VALOR"),
        ("score", "SCORE"),
    ]

    def cells_of(row):
        return [
            row["case"] if k == "case" else _fmt_pct(row[k]).strip() for k, _ in cols
        ]

    body = [cells_of(r) for r in rows]
    if rows:
        media = {k: sum(r[k] for r in rows) / len(rows) for k, _ in cols if k != "case"}
        body.append(
            ["MEDIA"] + [_fmt_pct(media[k]).strip() for k, _ in cols if k != "case"]
        )

    if markdown:
        out = [f"### Acuracia da extracao - provider `{provider_name}`\n"]
        out.append("| " + " | ".join(h for _, h in cols) + " |")
        out.append("|" + "|".join(["---"] * len(cols)) + "|")
        for i, cells in enumerate(body):
            if i == len(body) - 1 and rows:
                cells = [f"**{c}**" for c in cells]
            out.append("| " + " | ".join(cells) + " |")
        return "\n".join(out)

    # Largura por coluna, calculada do conteudo: nome de caso longo nao pode
    # empurrar a tabela e tornar o resultado ilegivel — e este texto e o que o
    # grupo vai olhar toda semana.
    headers = [h for _, h in cols]
    widths = [
        max(len(headers[i]), *(len(c[i]) for c in body)) if body else len(headers[i])
        for i in range(len(cols))
    ]

    def line(cells):
        return "  ".join(
            c.ljust(widths[i]) if i == 0 else c.rjust(widths[i])
            for i, c in enumerate(cells)
        )

    out = [f"\nProvider: {provider_name}", line(headers)]
    out.extend(line(c) for c in body)
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default=None, help="naive | rule_based | llm")
    parser.add_argument("--case", default=None, help="rodar so um caso, com detalhe")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    _load_django()
    from credit.financials.services.extraction import providers

    provider = providers.get_provider(args.provider)

    case_dirs = sorted(d for d in CASES_DIR.iterdir() if (d / "expected.json").exists())
    if args.case:
        case_dirs = [d for d in case_dirs if d.name == args.case]
        if not case_dirs:
            print(f"caso '{args.case}' nao existe em {CASES_DIR}", file=sys.stderr)
            return 2

    rows = [score_case(d, provider, verbose=bool(args.case)) for d in case_dirs]
    print(render_table(rows, provider.name, args.markdown))

    warned = {w for r in rows for w in r["warnings"]}
    if warned and not args.markdown:
        print("\nAvisos do provider:")
        for w in sorted(warned):
            print(f"  ! {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
