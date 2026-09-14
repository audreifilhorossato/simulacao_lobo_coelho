# Financials — repositório-semente

Case Insper Code Jr. 2026.2 · parceria com a **Astecha**

Este repositório é o **ponto de partida**, não um exemplo a copiar. Ele já traz
o que a Astecha exige que exista de determinada forma (modelo de dados, caminho
de escrita, conferências contábeis, as duas interfaces de migração) e deixa
explicitamente em aberto o que é o trabalho de vocês.

Leia o **case** e o **`ANEXO-TECNICO.md`** antes de escrever a primeira linha.

---

## Subir tudo

```bash
cp env.example .env
docker compose up
```

- API: <http://localhost:8000/api/v1/credit/financials/companies>
- Swagger: <http://localhost:8000/api/v1/docs/>
- Frontend: <http://localhost:5173>

O `migrate` roda sozinho na subida e semeia as **59 contas** do plano
padronizado. Confira:

```bash
curl "http://localhost:8000/api/v1/credit/financials/account-chart?page_size=500" | head
```

## Testes

```bash
docker compose exec backend pytest
```

56 testes acompanham o esqueleto e **todos passam** no estado em que você
recebeu. Se algum quebrar antes de você mexer em qualquer coisa, é problema de
ambiente — resolva antes de seguir.

## Acurácia da extração

```bash
docker compose exec backend python /app/../eval/run.py --provider naive
# ou, fora do container:
python eval/run.py --provider naive
```

Saída no estado inicial: **0,0% em tudo.** É o piso, e é de propósito — o
`NaiveProvider` não extrai nada. O seu trabalho é fazer esse número subir, e a
diferença entre os números é a sua apresentação final.

---

## O que já está pronto (não reescreva)

| Peça | Onde | Por que já vem pronta |
|---|---|---|
| 5 models | `backend/src/credit/financials/models/` | São o schema da Astecha, coluna por coluna. Renomear qualquer um quebra a migração. |
| Plano de contas (59 contas) | `services/chart_defaults.py` + migration `0002` | É a taxonomia que torna duas empresas comparáveis. Estender é `CUSTOM`; alterar `STANDARD` é bloqueado. |
| Caminho de escrita | `services/statement_service.py` | Validação em 2 fases, escrita atômica, idempotente pela chave natural. **É o alvo do seu pipeline.** |
| Conferências contábeis | `services/checks_service.py` | Ativo=Passivo+PL, fechamento da DRE, subtotal × filhos, sinal. Pode acrescentar; não relaxe. |
| API base + OpenAPI | `views/`, `urls.py` | Rotas, paginação e formato de erro no padrão da plataforma. |
| Arreio de avaliação | `eval/` | Transforma "melhorou" em número. |

## O que é trabalho de vocês

| # | Entrega | Sprint | Onde começar |
|---|---|---|---|
| 1 | Parse de PDF nativo, PDF escaneado (OCR) e XLSX | 1 | `tasks.py::parse_document` |
| 2 | `RuleBasedProvider` — extração sem IA | 1 | `services/extraction/providers/` |
| 3 | De-para `raw_label` → `account_code` | 1 | idem |
| 4 | `POST /documents/{id}/extract` (202 + polling) | 2 | `views/source_document.py` |
| 5 | Models `EXTRACTION` / `EXTRACTION_LINE` | 2 | `models/` |
| 6 | Tela de revisão lado a lado | 2 | `frontend/src/views/ReviewView.vue` |
| 7 | `LLMProvider` | 3 | `providers/` |
| 8 | Índices financeiros e comparabilidade | 4 | novo `services/indicators.py` |
| 9 | Covenant como fórmula + apuração | 4 | novo `services/covenants.py` |

Cada arquivo relevante tem um `TODO` no ponto exato onde o trabalho entra.

---

## As três regras que mais custam nota

1. **Não confie no banco.** O Snowflake, para onde este código vai, **não impõe
   FK nem UNIQUE e não tem trava de linha.** Unicidade e integridade se validam
   em código; trava de escrita mora no Redis. Se você escrever
   `select_for_update` ou depender de `IntegrityError`, funciona no Postgres e
   falha silenciosamente em produção.

2. **Nada de SQL específico de Postgres.** Sem `ON CONFLICT`, `RETURNING`,
   `DISTINCT ON`, `ILIKE` cru, `ArrayField`/`JSONField` do Postgres, extensão
   (`pgvector`, `uuid-ossp`). Use o ORM; para upsert, `update_or_create`.

3. **O SDK do LLM só existe dentro de `providers/`.** Um `import anthropic` na
   camada de service transforma a migração de "trocar um arquivo" em
   "reescrever o app".

O `ANEXO-TECNICO.md` traz as 15 regras completas, com o motivo de cada uma.

---

## Estrutura

```
backend/
  config/                     settings, urls, celery
  src/credit/financials/
    models/                   as 5 tabelas (nao renomear)
    serializers/              entrada e saida da API
    views/                    ViewSets FINAS — logica vai em services/
    services/
      statement_service.py    o caminho de escrita (o alvo do pipeline)
      checks_service.py       conferencias contabeis
      account_chart_service.py
      chart_defaults.py       as 59 contas
      storage.py              << COSTURA DE MIGRACAO 1 (arquivo)
      extraction/
        types.py              ParsedDocument, StatementDraft, DraftLine
        providers/base.py     << COSTURA DE MIGRACAO 2 (IA)
        providers/naive.py    o piso (0%)
    migrations/               0001 schema, 0002 seed do plano
    tests/                    56 testes — modelo para os seus
    tasks.py                  Celery: o UNICO caminho assincrono
frontend/                     Vue 3 + Vite + Tailwind (5 telas)
eval/                         arreio de acuracia + 3 casos com gabarito
.github/workflows/ci.yml      lint, testes, migrations, OpenAPI, acuracia
```

## Convenções de trabalho

- **Branch por tarefa**, PR para `main`, revisão de outra pessoa antes do merge.
- **CI verde é condição de merge.** Não desative job para "passar".
- **Um teste por comportamento novo.** O `pytest` roda em segundos; use-o.
- **`.env` nunca é commitado.** Chave de API no histórico do Git é critério de
  reprovação — e trocar o arquivo depois não resolve: o valor fica no histórico
  para sempre. Se acontecer, **revogue a chave primeiro**.
