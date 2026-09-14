# Anexo Técnico — App Financials

**Case Insper Code Jr. 2026.2 · Astecha**
Complemento obrigatório do documento de case. Onde os dois divergirem, vale o case.

---

## Sumário

1. [Como usar este documento](#1-como-usar-este-documento)
2. [O contrato de migração — as 15 regras](#2-o-contrato-de-migração--as-15-regras)
3. [Dicionário de dados](#3-dicionário-de-dados)
4. [Contrato de API](#4-contrato-de-api)
5. [As 12 sujeiras do mundo real](#5-as-12-sujeiras-do-mundo-real)
6. [Índices financeiros e a ponte com covenants](#6-índices-financeiros-e-a-ponte-com-covenants)
7. [Definition of Done por sprint](#7-definition-of-done-por-sprint)
8. [Checklist de migração](#8-checklist-de-migração)

---

## 1. Como usar este documento

O projeto tem uma característica que o diferencia de um trabalho de faculdade
comum: **o código de vocês vai ser plugado numa plataforma que já existe e está
em produção.** Isso é uma oportunidade — o trabalho não morre no fim do semestre
— e é também uma restrição, porque a plataforma tem um formato e ele não é
negociável.

A boa notícia é que a restrição é pequena e está toda escrita aqui. São 15
regras, e nenhuma delas é arbitrária: cada uma existe porque a violação dela já
causou um problema real. Elas estão anotadas com o motivo justamente para vocês
poderem julgar quando uma situação nova cai ou não na regra.

O repositório-semente já obedece a todas as 15. Se vocês seguirem o padrão dos
arquivos que já estão lá, obedecem por tabela.

### O contexto em uma página

A Astecha opera uma plataforma de gestão de fundos de investimento
(FIIs, CRIs, CRAs, renda fixa). Um dos módulos, o **Obligations**, controla as
obrigações contratuais de operações de crédito — inclusive os **covenants
financeiros**: cláusulas do tipo *"a dívida líquida da empresa devedora não pode
passar de 3× o EBITDA, apurado trimestralmente"*.

Para verificar um covenant desses é preciso ter as demonstrações financeiras da
empresa devedora, **padronizadas**. E é aí que o processo trava: as empresas
mandam balanço e DRE em PDF escaneado, em planilha bagunçada, cada uma com um
plano de contas próprio, escalas diferentes, convenções de sinal diferentes.
Hoje um analista transcreve isso à mão, empresa por empresa, trimestre a
trimestre.

**O app Financials existe para eliminar essa transcrição.** Ele já tem o
esqueleto — cadastro, plano de contas padronizado, tabela de documentos, o
caminho de escrita das demonstrações e as conferências contábeis. O que ele não
tem é justamente o miolo: **ler o documento bagunçado e produzir a demonstração
padronizada.**

É esse miolo que vocês vão construir.

---

## 2. O contrato de migração — as 15 regras

Vale **25% da nota específica**, verificada por checklist objetivo **e** por uma
tentativa real de plugar o código de vocês na plataforma.

### Estrutura

**R1 — Estrutura de pastas idêntica.**
`backend/src/credit/financials/{models,serializers,views,services,tests}/` mais
`urls.py` e `tasks.py`. Um arquivo por model, por serializer e por view.
*Por quê:* a migração é literalmente copiar pastas. Uma organização diferente,
mesmo que melhor, transforma isso em trabalho de tradução.

**R4 — Lógica de negócio em `services/`, ViewSet fina.**
A view valida a entrada, chama o service e responde. Nada de regra de negócio
dentro do ViewSet.
*Por quê:* a mesma regra é chamada por três superfícies diferentes na plataforma
(HTTP, tarefa Celery, ferramenta de agente). Regra que vive na view só existe
para uma delas.

### Banco de dados

**R2 — Todo campo declara `db_column="NOME_MAIÚSCULO"`, e `db_table` bate com o
nome da Astecha.**
```python
id = models.BigAutoField(primary_key=True, db_column="COMPANY_ID")

class Meta:
    db_table = "FINANCIALS_COMPANY"
```
*Por quê:* o Snowflake é sensível a maiúsculas e guarda identificadores em
maiúsculo. Sem o `db_column`, o Django gera `company_id` minúsculo e a tabela
simplesmente não é a mesma.

**R3 — `managed = True` em todo model novo.**
*Por quê:* na plataforma esse flag *é* a decisão de migration — o roteador
decide o que migra a partir dele.

**R5 — Zero SQL específico de Postgres.**
Proibidos: `ON CONFLICT`, `RETURNING`, `DISTINCT ON`, `ILIKE` cru,
`ArrayField`/`HStoreField`/`JSONField` do `django.contrib.postgres`, extensões
(`pgvector`, `uuid-ossp`), `SERIAL` explícito, *full-text search* do Postgres.
Para upsert: `Model.objects.update_or_create(...)`. Para busca textual:
`__icontains` (o ORM traduz para o dialeto certo).
*Por quê:* o destino é Snowflake. Nada disso existe lá.

**R6 — A aplicação não pode confiar em constraint de banco.**
Esta é a regra que mais surpreende, e a mais importante. **O Snowflake não impõe
chave estrangeira, não impõe `UNIQUE` e não tem trava de linha.** Ele *aceita* a
declaração e a ignora.

Consequências práticas:
- `unique_together` é a **chave natural** do registro, não uma garantia. Quem
  garante é o código.
- Não existe `select_for_update()`. Trava de escrita vai no Redis
  (`caches["shared"]`), como o `statement_service` já faz.
- Nunca use `IntegrityError` como controle de fluxo: no Snowflake ele não vem.
- Valide existência de referência **antes** de escrever, não depois.

*Por quê:* código que depende do banco para barrar duplicata passa em todos os
testes no Postgres e escreve dado duplicado em produção, em silêncio. É um
defeito que não aparece em revisão de código nem em teste local.

**R14 — Schema só por migration do Django.**
Nada de DDL aplicado à mão, nem de `RunSQL` com `CREATE OR REPLACE TABLE`.
*Por quê:* o deploy da plataforma aplica as migrations em várias contas de
cliente. O que não está numa migration não existe em produção.

### Assíncrono

**R7 — Celery + Redis é o único mecanismo assíncrono.**
Proibidos: `threading`, `concurrent.futures`, `BackgroundTasks`,
`asyncio.create_task`, `while True` com `sleep`. A ViewSet enfileira e devolve
**202** com `task_id`; existe endpoint de consulta de status.

Duas regras derivadas, que valem nota:
- **A lógica não mora na task.** A task orquestra e chama o service.
- **Task não se reagenda.** Nada de `apply_async(countdown=...)` no fim de uma
  task, nem `self.retry()` usado como agendador — isso cria laço que duplica a
  cada restart.

*Por quê:* a aplicação roda em muitos processos. Trabalho que vive na memória de
um deles não existe para os outros e desaparece no primeiro *deploy*. E o parse
de um PDF escaneado leva minutos: dentro da requisição, estoura o *timeout* do
servidor e o usuário vê 502 com o trabalho perdido no meio.

### As duas costuras de migração

Estas duas são o que faz a diferença entre "a Astecha pluga em uma tarde" e "a
Astecha reescreve".

**R8 — Provider de IA atrás de interface.**
`services/extraction/providers/base.py` define
`ExtractionProvider.extract(ParsedDocument) -> ExtractionResult`.
**Nenhum `import anthropic` / `openai` / `google.generativeai` / `ollama` pode
existir fora de `providers/`.** Chave de API só por `os.environ`, e só lida
dentro do módulo do provider.
*Por quê:* na Astecha o provider vira Snowflake Cortex ou a API da Anthropic
rodando dentro da conta do cliente (o dado do cliente não pode sair de lá). Se o
SDK estiver espalhado, a troca deixa de ser um arquivo.

**R9 — Armazenamento atrás de interface, com a assinatura da plataforma.**
`services/storage.py` tem **exatamente** estas quatro funções, com estes
argumentos, nesta ordem:
```python
put_file(file_bytes: bytes, company_id, year: int, month: int, file_name: str) -> str
get_file(company_id, year: int, month: int, file_name: str) -> bytes
list_files(company_id, year: int, month: int) -> list[dict]
remove_file(company_id, year: int, month: int, file_name: str) -> str
```
Layout de caminho: `{COMPANY_ID}/{YYYY}/{MM}/{arquivo}`. `put_file` devolve o
caminho **relativo** — é ele que vai para `SOURCE_DOCUMENT.STAGE_PATH`, nunca um
caminho absoluto do disco de vocês.
*Por quê:* na plataforma essas quatro funções viram `PUT`/`GET`/`LIST`/`REMOVE`
num *stage* interno do Snowflake. Assinatura igual = trocar um arquivo.
`backend/.../tests/test_storage.py` trava isso, e esses testes continuam
passando depois da troca.

### API

**R10 — Rotas em `/api/v1/credit/financials/…`, `DefaultRouter(trailing_slash=False)`.**
*Por quê, e não é preciosismo:* com `trailing_slash=True`, o `APPEND_SLASH` do
Django responde um **301** a quem chama sem a barra — e o corpo do POST é
descartado no redirect. O sintoma é uma escrita que "some" sem erro nenhum.

**R11 — Envelope de paginação `{count, next, previous, results}`; serializers de
tabela expõem as chaves em MAIÚSCULA.**
A escrita aceita maiúscula **ou** minúscula: um payload montado copiando uma
resposta tem que funcionar.
*Por quê:* o frontend da plataforma já lê exatamente nesse formato.

**R13 — OpenAPI por `drf-spectacular`; todo endpoint no schema.**
Use `@extend_schema` para upload, ações customizadas e polling; declare os
parâmetros de query com `OpenApiParameter`.
*Por quê:* é gate de CI na plataforma, e é como a Astecha descobre o que vocês
construíram sem ler o código todo.

### Qualidade

**R12 — Testes com `pytest` + `rest_framework.test.APIClient`.**
Um arquivo por recurso (`tests/test_{recurso}.py`). **Mocke serviços, nunca
`Model.objects`.** Cubra: status, formato da resposta, paginação, filtro, lista
vazia, parâmetro inválido, erro esperado.
*Por quê:* teste que mocka o ORM testa o mock. E o corretor lê o teste antes de
ler a implementação: um teste de lista vazia diz mais sobre cuidado do que
qualquer README.

**R15 — Zero dado de cliente, zero segredo no repositório.**
`env.example` sim, `.env` nunca. Se uma chave for commitada por acidente:
**revogue a chave no provedor primeiro**, depois limpe o histórico — trocar o
arquivo no commit seguinte não adianta, o valor fica no histórico para sempre.
*Por quê:* é critério de reprovação, e é o tipo de erro que não dá para
desfazer.

---

## 3. Dicionário de dados

### 3.1 O que já existe (não renomeie, não redefina)

#### `FINANCIALS_COMPANY`

| Coluna | Tipo | Notas |
|---|---|---|
| `COMPANY_ID` | bigint PK | |
| `NAME` | varchar(255) | razão social |
| `CNPJ` | varchar(18) | chave natural; 14 dígitos, sem máscara |
| `PROJECT_ID` | varchar(200) null | referência **soft** ao cadastro da plataforma |
| `DEAL_ID` | varchar(200) null | idem — **não** transforme em ForeignKey |
| `STATUS` | varchar(20) | `ACTIVE` \| `INACTIVE` |
| `CREATED_AT` / `UPDATED_AT` | timestamp | |

> `PROJECT_ID`/`DEAL_ID` são texto e não FK porque, na plataforma, esses
> cadastros vivem em outro alias de banco e o roteador bloqueia relação entre
> aliases. O join é feito em Python, nunca em SQL.

#### `FINANCIALS_ACCOUNT_CHART` — o plano padronizado

| Coluna | Tipo | Notas |
|---|---|---|
| `ACCOUNT_CODE` | varchar(30) PK | pontuado: `1.01.01` |
| `ACCOUNT_NAME` | varchar(255) | |
| `ACCOUNT_TYPE` | varchar(20) | `ASSET` \| `LIABILITY` \| `EQUITY` \| `REVENUE` \| `EXPENSE` \| `RESULT` |
| `STATEMENT` | varchar(20) | `BALANCE_SHEET` \| `INCOME_STATEMENT` |
| `PARENT_CODE` | FK self, null | |
| `LEVEL` | smallint | 1 a 4 |
| `DISPLAY_ORDER` | int | |
| `ORIGIN` | varchar(20) | `STANDARD` (imutável) \| `CUSTOM` |

**59 contas, 3 níveis, 6 grupos.** `ACCOUNT_TYPE`, `STATEMENT`, `LEVEL` e
`PARENT_CODE` são **derivados** do código, nunca informados — é isso que torna
"uma DESPESA pendurada no ATIVO" impossível de representar, e não apenas
desaconselhada.

| Grupo | Tipo | Demonstração |
|---|---|---|
| `1` Ativo | ASSET | Balanço |
| `2` Passivo | LIABILITY | Balanço |
| `3` Patrimônio Líquido | EQUITY | Balanço |
| `4` Receitas | REVENUE | DRE |
| `5` Custos e Despesas | EXPENSE | DRE |
| `6` Resultado | RESULT | DRE |

Duas coisas importantes:

- **Grupo 6 (`RESULT`) não é receita nem despesa.** São os subtotais que a DRE
  *imprime* ("Lucro Bruto", "EBIT", "Lucro Líquido"). Eles são excluídos de toda
  soma e usados só como **conferência** — é a melhor validação disponível:
  total impresso × total calculado a partir das folhas.
- **Códigos terminados em `.09`/`.9` são a saída "Outros"**, deliberada. Uma
  linha que não casa com nada tem uma casa honesta, em vez de ser empurrada para
  uma conta específica à qual não pertence. Use-os — e registre o rótulo
  original em `NOTES`.

O CSV completo está em `plano-de-contas-padronizado.csv` e em
`backend/src/credit/financials/data/standard_chart.csv`.

#### `FINANCIALS_SOURCE_DOCUMENT`

| Coluna | Tipo | Notas |
|---|---|---|
| `DOCUMENT_ID` | bigint PK | |
| `COMPANY_ID` | FK | |
| `STAGE_PATH` | varchar(1000) **unique** | relativo: `{COMPANY_ID}/{YYYY}/{MM}/{arquivo}` |
| `ORIGINAL_FILENAME` | varchar(500) | |
| `FILE_TYPE` | varchar(10) | `PDF` \| `XLSX` |
| `UPLOAD_DATE` | timestamp | |
| `PROCESSING_STATUS` | varchar(20) | `PENDING` \| `PARSING` \| `PARSED` \| `FAILED` |
| `PARSED_TEXT` | text null | saída do parse |

#### `FINANCIALS_STATEMENT`

| Coluna | Tipo | Notas |
|---|---|---|
| `STATEMENT_ID` | bigint PK | |
| `COMPANY_ID` | FK | |
| `SOURCE_DOCUMENT_ID` | FK null | rastreabilidade até o arquivo |
| `STATEMENT_TYPE` | varchar(20) | `BALANCE_SHEET` \| `INCOME_STATEMENT` |
| `PERIOD_END_DATE` | date | **sempre o último dia do mês** |
| `PERIOD_TYPE` | varchar(20) | `MONTHLY` \| `QUARTERLY` \| `ANNUAL` |
| `CURRENCY` | varchar(3) | `BRL` |
| `STATUS` | varchar(20) | `DRAFT` \| `FINAL` |
| `EXTRACTED_BY` | varchar(100) null | |

Chave natural: **(`COMPANY_ID`, `STATEMENT_TYPE`, `PERIOD_END_DATE`)**.

#### `FINANCIALS_STATEMENT_LINE`

| Coluna | Tipo | Notas |
|---|---|---|
| `LINE_ID` | bigint PK | |
| `STATEMENT_ID` | FK cascade | |
| `ACCOUNT_CODE` | FK **PROTECT** | a conta padronizada |
| `RAW_LABEL` | varchar(500) | **o rótulo como estava no documento** |
| `VALUE` | decimal(20,2) | já com escala e sinal na convenção de destino |
| `NOTES` | text null | |

> `RAW_LABEL` é obrigatório e nunca deve ser "limpo". Sem ele ninguém consegue
> auditar o de-para — e é ele que alimenta o aprendizado do mapeamento.

### 3.2 O que vocês acrescentam

Nomes sugeridos; o formato é decisão de vocês, desde que respeite R2/R3/R6.

#### `FINANCIALS_EXTRACTION` — uma tentativa de extração

`EXTRACTION_ID`, `DOCUMENT_ID` (FK), `PROVIDER`, `MODEL`, `PROMPT_VERSION`,
`STATUS`, `LATENCY_MS`, `COST_USD`, `ERROR`, `CREATED_AT`.

> Guardem `PROVIDER`, `MODEL` e `PROMPT_VERSION`. Sem isso não dá para responder
> *"a acurácia caiu depois de qual mudança?"* — e essa pergunta vai aparecer.

#### `FINANCIALS_EXTRACTION_LINE` — o rascunho

`LINE_ID`, `EXTRACTION_ID` (FK), `RAW_LABEL`, `RAW_VALUE` (texto, como estava),
`PAGE`, `SCALE_FACTOR`, `SUGGESTED_ACCOUNT_CODE`, `CONFIDENCE` (0–1),
`CONFIRMED_ACCOUNT_CODE`, `CONFIRMED_BY`, `CONFIRMED_AT`.

> É a tabela mais importante do que vocês vão criar. Ela é ao mesmo tempo o que
> a tela de revisão edita, o que a métrica de acurácia mede e o que alimenta a
> memória de de-para. Guardem **sugerido** e **confirmado** em colunas
> separadas: colapsar os dois destrói a medida.

#### `FINANCIALS_INDICATOR_DEF` — definição de índice

`INDICATOR_CODE` (PK), `NAME`, `FORMULA`, `UNIT`, `STATEMENT_SCOPE`.

#### `FINANCIALS_COVENANT_RULE` — o covenant como fórmula

`RULE_ID`, `COMPANY_ID` (FK), `DEAL_ID` (soft), `INDICATOR_CODE` (FK),
`OPERATOR` (`<=`, `<`, `>=`, `>`), `THRESHOLD` (decimal), `PERIODICITY`,
`SOURCE_TEXT` (a cláusula original), `CLAUSE_REF`, `STATUS`.

#### `FINANCIALS_COVENANT_CHECK` — a apuração

`CHECK_ID`, `RULE_ID` (FK), `STATEMENT_ID` (FK), `MEASURED_VALUE`, `STATUS`
(`CUMPRIDO` \| `DESCUMPRIDO` \| `SEM_DADO`), `CHECKED_AT`, `DETAIL` (as parcelas
que formaram o valor).

#### *(stretch)* `FINANCIALS_MAPPING_MEMORY`

`COMPANY_ID`, `NORMALIZED_LABEL`, `ACCOUNT_CODE`, `CONFIRMATIONS`, `LAST_SEEN`.

---

## 4. Contrato de API

Base: `/api/v1/credit/financials/` · **sem barra no fim** · paginação
`{count, next, previous, results}` · chaves em MAIÚSCULA.

### Já existe

| Método | Rota | O que faz |
|---|---|---|
| `GET` `POST` `PATCH` | `/companies` | cadastro (filtros: `status`, `search`) |
| `GET` | `/account-chart` | plano de contas (filtros: `statement`, `origin`, `level`) |
| `POST` | `/account-chart/upsert` | cria/atualiza contas `CUSTOM` em lote |
| `GET` | `/documents` | documentos (filtros: `company_id`, `status`) |
| `POST` | `/documents/upload` | multipart → cria `SOURCE_DOCUMENT` `PENDING` |
| `GET` | `/statements` | demonstrações (filtros: `company_id`, `statement_type`, `status`, `period_from`, `period_to`) |
| `POST` | `/statements/validate` | valida sem escrever — sempre 200, erro vem como dado |
| `POST` | `/statements/write` | escreve em lote, atômico, idempotente |
| `GET` | `/statements/{id}/checks` | conferências contábeis |
| `DELETE` | `/statements/{id}` | só `DRAFT` |

#### O payload de `/statements/write` — o alvo do pipeline

```json
{
  "COMPANY_ID": 1,
  "STATEMENTS": [
    {
      "STATEMENT_TYPE": "BALANCE_SHEET",
      "PERIOD_END_DATE": "2025-12-31",
      "PERIOD_TYPE": "ANNUAL",
      "CURRENCY": "BRL",
      "SOURCE_DOCUMENT_ID": 7,
      "OVERWRITE": false,
      "LINES": [
        {"ACCOUNT_CODE": "1.01.01", "RAW_LABEL": "Caixa e equivalentes de caixa", "VALUE": "150000.00"},
        {"ACCOUNT_CODE": "2.01.01", "RAW_LABEL": "Fornecedores", "VALUE": "310000.00"},
        {"ACCOUNT_CODE": "3.01", "RAW_LABEL": "Capital social", "VALUE": "400000.00"}
      ]
    }
  ]
}
```

Garantias que vocês herdam de graça, e que **não devem reimplementar**:

- **Duas fases.** A validação é só leitura e é *a mesma função* usada pelo
  `/validate`. Não existe segunda cópia das regras para divergir.
- **Atômico.** Se qualquer demonstração do lote falhar, nada é escrito.
- **Idempotente.** Reenviar o mesmo payload converge para o mesmo
  `STATEMENT_ID`. Reenviar depois de um *timeout* de rede é sempre seguro.
- **Substituição total das linhas**, nunca merge — um merge não consegue
  expressar "esta linha foi removida" e deixaria linha fantasma somando.
- **Conferência não bloqueia.** Um balanço que não fecha é **gravado**, com o
  aviso junto. Isso é decisão de produto: o documento do cliente às vezes não
  fecha mesmo, e recusar a escrita empurraria o operador a amassar números até a
  API aceitar. Um sistema de registro que empurra seu operador a falsificar dado
  falhou na sua única função.

Erros: `400` payload inválido · `404` não existe · `409` conflito de estado
(gravação concorrente na mesma chave, ou substituição de `FINAL` sem
`OVERWRITE`).

### Vocês constroem

| Método | Rota | Resposta |
|---|---|---|
| `POST` | `/documents/{id}/extract` | **202** `{TASK_ID, EXTRACTION_ID}` |
| `GET` | `/extractions/{id}` | rascunho: linhas, conta sugerida, confiança, checks |
| `GET` | `/extractions/{id}/status` | polling do job |
| `PATCH` | `/extractions/{id}/lines/{line_id}` | analista corrige o de-para |
| `POST` | `/extractions/{id}/approve` | monta o payload acima e chama `write_statements` |
| `GET` | `/extractions/metrics` | acurácia agregada por provider |
| `GET` | `/indicators?company_id=&period=` | índices calculados |
| `GET` | `/indicators/compare?company_ids=&indicator=&periods=` | comparabilidade |
| `GET` `POST` | `/covenant-rules` | covenant como fórmula |
| `GET` | `/covenant-checks?company_id=` | apuração com status e rastro |

---

## 5. As 12 sujeiras do mundo real

Esta é a lista do que efetivamente faz o problema ser difícil. Ela não é
teórica: cada item aparece em documentos reais toda semana. Tratem como
requisito, não como curiosidade — e escrevam um teste para cada.

**1. Escala.** *"Em R$ mil"*, *"Em milhares de reais"*, *"R$ MM"*, *"valores em
milhares, exceto lucro por ação"*. Errar é errar por **1000×**: o erro mais
barato de cometer e o mais caro de descobrir. Detecte e registre o fator; não
deduza pelo tamanho do número.

**2. Sinal.** A mesma despesa vem `1.234`, `-1.234` ou `(1.234)` dependendo do
documento. A convenção de **destino** é `EXPENSE` **positiva** (o
`checks_service` calcula receita − despesa). Exceção real: `4.02 Deduções da
Receita Bruta` pertence ao grupo 4 (receita) e entra **negativa** — isso dispara
o aviso de sinal, e o aviso está certo sobre um dado certo.

**3. Número em pt-BR.** `1.234.567,89` × `1,234,567.89`. E `-`, `–`, `—` ou
célula vazia significam zero, não "faltando".

**4. Várias colunas de período.** Um balanço quase sempre traz o ano corrente e
o anterior lado a lado. **Cada coluna é uma demonstração diferente.** Ler só a
primeira perde metade do documento; juntar as duas grava o ano errado sem nunca
dar erro.

**5. Subtotal impresso junto com a quebra.** O PDF imprime "Ativo Circulante
1.000" **e** as contas que somam 1.000. Somar tudo dobra. A regra da plataforma:
**só folhas somam; pai presente é conferência.** O `checks_service` já
implementa isso — não reimplemente diferente.

**6. Conta que não existe no plano.** "Adiantamento a fornecedores" e o plano
não tem. Duas saídas legítimas: mapear para o pai mais próximo (ou o `.09`
"Outros") registrando o rótulo em `NOTES`, ou criar uma conta `CUSTOM` filha.
**Descartar em silêncio nunca é opção** — some dinheiro do balanço.

**7. `PERIOD_END_DATE` é sempre o último dia do mês.** *"Exercício findo em 31
de dezembro de 2025"* → `2025-12-31`, `ANNUAL`. Um `2025-12-30` vindo do OCR é
erro de leitura, não competência nova — e o `statement_service` recusa.

**8. DRE acumulada × do período.** "3º trimestre" pode ser 01/07–30/09 ou
01/01–30/09. Muda tudo, e o documento nem sempre diz. Quando não der para
decidir, **marque baixa confiança e deixe o analista escolher** — chutar aqui é
pior que perguntar.

**9. Linhas de dedução.** "(−) Deduções da receita bruta", "(−) Depreciação e
amortização": sinal *e* hierarquia ao mesmo tempo.

**10. XLSX bagunçado.** Células mescladas, cabeçalho na linha 7, colunas
inteiramente vazias entre as que importam, nota de rodapé no meio da tabela,
várias abas (uma por trimestre), número armazenado como texto, e a linha de
total em negrito sem nenhuma outra marca que a distinga.

**11. PDF escaneado e torto.** Precisa de OCR, e o OCR troca `0`/`O` e `1`/`l`,
perde o separador de milhar e junta colunas quando a página está inclinada.
Documento em que o OCR falhou tem que virar `FAILED` com motivo — **nunca ficar
preso em `PARSING` para sempre.**

**12. Identificar a empresa.** CNPJ e razão social vêm do papel e precisam casar
com o cadastro. Um dígito de CNPJ trocado pelo OCR é comum: o comportamento
certo é **avisar**, não recusar.

---

## 6. Índices financeiros e a ponte com covenants

É aqui que a padronização deixa de ser arrumação e vira produto.

### Índices mínimos

| Código | Índice | Fórmula (sobre o plano padronizado) |
|---|---|---|
| `LIQ_CORRENTE` | Liquidez corrente | Ativo Circulante ÷ Passivo Circulante |
| `LIQ_SECA` | Liquidez seca | (Ativo Circulante − Estoques) ÷ Passivo Circulante |
| `ENDIVIDAMENTO` | Endividamento geral | (Passivo Circ. + Não Circ.) ÷ Ativo Total |
| `DIVIDA_LIQUIDA` | Dívida líquida | Empréstimos (CP + LP) + Debêntures − Caixa − Aplicações |
| `EBITDA` | EBITDA | EBIT (`6.03`) + Depreciação e Amortização (`5.04`) |
| `DL_EBITDA` | Alavancagem | Dívida Líquida ÷ EBITDA |
| `COBERTURA_JUROS` | Cobertura de juros | EBIT ÷ Despesas Financeiras |
| `MARGEM_LIQUIDA` | Margem líquida | Lucro Líquido ÷ Receita Líquida |
| `ROE` | Retorno sobre PL | Lucro Líquido ÷ Patrimônio Líquido |

Três cuidados que separam um cálculo correto de um bonito:

- **Divisão por zero e por ausência são coisas diferentes.** EBITDA zero e
  EBITDA não apurado (a DRE não veio) produzem resultados diferentes: o primeiro
  é infinito, o segundo é `SEM_DADO`. Não retorne `0` para os dois.
- **Somar folhas, não pais** — o mesmo cuidado do `checks_service`.
- **Guardem as parcelas, não só o resultado.** "Dívida líquida = 4,2M" sem
  mostrar de onde saiu é um número que ninguém consegue defender numa reunião — e
  defender o número é exatamente o uso.

### O covenant

Hoje, na plataforma, um covenant é **texto**: uma cláusula, uma categoria, uma
periodicidade, um responsável. **Não existe fórmula, não existe limite numérico,
não existe apuração.** Alguém lê a cláusula, olha o balanço e decide.

O que vocês constroem é a ponte: transformar

> *"A Devedora deverá manter, ao final de cada trimestre, índice de Dívida
> Líquida sobre EBITDA não superior a 3,00 (três inteiros)."*

em

```json
{
  "INDICATOR_CODE": "DL_EBITDA",
  "OPERATOR": "<=",
  "THRESHOLD": "3.00",
  "PERIODICITY": "TRIMESTRAL",
  "SOURCE_TEXT": "A Devedora devera manter, ao final de cada trimestre, ...",
  "CLAUSE_REF": "5.1(i)"
}
```

e, quando uma demonstração é aprovada, apurar automaticamente:

```json
{
  "STATUS": "DESCUMPRIDO",
  "MEASURED_VALUE": "3.41",
  "THRESHOLD": "3.00",
  "DETAIL": {
    "DIVIDA_LIQUIDA": "4200000.00",
    "EBITDA": "1232000.00",
    "PARCELAS": {"2.01.02": "...", "2.02.01": "...", "1.01.01": "..."}
  }
}
```

**Escopo mínimo aceitável:** uma gramática restrita (um índice, um operador, um
limite) e a apuração automática no `approve`. Não construam um interpretador de
expressões genérico — não cabe no semestre, e a maioria esmagadora dos covenants
financeiros cabe nessa forma simples.

**`SEM_DADO` é um resultado de primeira classe**, não um erro. Se a DRE do
trimestre não chegou, o covenant não está cumprido nem descumprido: ele não foi
apurado. Confundir os dois é como um relatório de compliance mente.

---

## 7. Definition of Done por sprint

### Sprint 0 — Fundação · entrega **11/09**

- [ ] `docker compose up` sobe os cinco serviços num comando, em máquina limpa
- [ ] `migrate` roda e o `GET /account-chart` devolve **59** contas
- [ ] `pytest` verde (os 56 que já vêm)
- [ ] `python eval/run.py --provider naive` roda e imprime 0%
- [ ] Documento de requisitos e backlog priorizado
- [ ] README v1: como subir, como testar, quem faz o quê
- [ ] Repositório organizado: branches, PRs, papéis definidos
- [ ] **Massa de dados v1**: ≥10 documentos públicos (CVM/B3) baixados, e ao
      menos 3 já degradados (impressos e escaneados, ou re-salvos como imagem)

### Sprint 1 — Fatia fina · entrega **05/10**

- [ ] Parse de PDF nativo funcionando (texto + tabelas)
- [ ] `RuleBasedProvider` registrado e passando em `test_provider_contract.py`
- [ ] `python eval/run.py --provider rule_based` com **SCORE > 0** e o número
      registrado no README
- [ ] Fluxo completo pelo menos uma vez: upload → parse → rascunho → aprovação →
      `STATEMENT` gravado
- [ ] Testes cobrindo pelo menos 4 das 12 sujeiras
- [ ] CI verde
- [ ] Planejado × realizado da Sprint 0

### Sprint 2 — Produto · **05/10 → 20/10**

- [ ] `POST /documents/{id}/extract` devolvendo **202**, com polling funcionando
- [ ] Documento que quebra o parser vira `FAILED` com motivo visível e opção de
      repetir — **nunca preso em `PARSING`**
- [ ] Tela de revisão: documento ao lado do rascunho
- [ ] Distinção visual entre "IA sugeriu" e "humano confirmou"
- [ ] Lista ordenada por confiança crescente (o difícil primeiro)
- [ ] Conferências contábeis recalculando ao vivo na correção
- [ ] Aprovar desabilitado enquanto houver linha sem conta

### Sprint 3 — IA · **20/10 → 27/10**

- [ ] `LLMProvider` registrado, com `temperature=0`
- [ ] Nenhum `import` de SDK de LLM fora de `providers/` *(grep no CI)*
- [ ] Confiança calibrada: linha de confiança baixa é mesmo a que o humano
      corrige
- [ ] **Tabela comparativa** `naive` × `rule_based` × `llm` nas 6 métricas
- [ ] Custo e latência por documento medidos
- [ ] Modo offline/mock para o CI (teste que chama API paga não roda no CI)

### Sprint 4 — Fechamento · **27/10 → 30/10**

- [ ] Os 9 índices calculados, com as parcelas guardadas
- [ ] Comparação de ≥2 empresas no mesmo índice, e de uma empresa em ≥2 períodos
- [ ] Covenant cadastrado como fórmula e apurado no `approve`, com
      `CUMPRIDO`/`DESCUMPRIDO`/`SEM_DADO`
- [ ] Cobertura de teste nas regras de padronização e no de-para
- [ ] CI verde, incluindo o job de acurácia
- [ ] Vídeo demo (≤5 min) do fluxo completo
- [ ] Documentação técnica: decisões, o que ficou de fora e **por quê**
- [ ] Apresentação com a curva de acurácia e o tempo por documento

---

## 8. Checklist de migração

O que a Astecha vai conferir, item a item, na entrega. Rodem isso antes de
entregar — é literalmente a folha de correção do critério nº 2.

**Estrutura e schema**
- [ ] Pastas em `backend/src/credit/financials/{models,serializers,views,services,tests}/`
- [ ] Todo campo com `db_column` em MAIÚSCULA; todo `db_table` em MAIÚSCULA
- [ ] `managed = True` em todo model
- [ ] Nenhum model existente renomeado ou com coluna removida
- [ ] `python manage.py makemigrations --check --dry-run` → "No changes detected"

**Portabilidade Postgres → Snowflake**
- [ ] `grep -rn "ON CONFLICT\|RETURNING\|DISTINCT ON\|ILIKE" backend/src` → vazio
- [ ] `grep -rn "django.contrib.postgres\|select_for_update" backend/src` → vazio
- [ ] Nenhum `except IntegrityError` usado como controle de fluxo
- [ ] Trava de escrita usa `caches["shared"]`, não o banco

**Costuras**
- [ ] `grep -rn "import anthropic\|import openai\|google.generativeai\|import ollama" backend/src | grep -v "/providers/"` → vazio
- [ ] As 4 funções de `storage.py` com a assinatura original
- [ ] `pytest src/credit/financials/tests/test_storage.py` verde
- [ ] `pytest src/credit/financials/tests/test_provider_contract.py` verde com **todos** os providers listados

**Assíncrono**
- [ ] `grep -rn "threading\|concurrent.futures\|asyncio.create_task" backend/src` → vazio
- [ ] Toda task em `tasks.py`; nenhuma task se reagenda
- [ ] Endpoint de extração devolve 202 com `task_id`

**API e qualidade**
- [ ] Rotas sob `/api/v1/credit/financials/`, sem barra no fim
- [ ] `python manage.py spectacular --file /tmp/schema.yml` sem erro, e todo
      endpoint novo aparece nele
- [ ] `pytest` verde; CI verde
- [ ] `.env` não está no repositório; `git log -p | grep -i "api.key\|sk-ant\|sk-"` → nada

**Entregáveis**
- [ ] README explica como subir do zero e um dev de fora consegue seguir
- [ ] `eval/run.py` roda e a tabela dos três providers está no README
- [ ] Documentação diz o que ficou de fora e por quê

---

## Suporte

Dúvida sobre o domínio (contabilidade, covenants, o que a plataforma espera) ou
sobre a arquitetura: usem o canal combinado. Há uma sessão técnica de 30 minutos
por sprint.

Duas coisas valem mais do que parecem, e contam a favor na avaliação:

- **Perguntar cedo.** Uma dúvida de domínio resolvida em 10 minutos de conversa
  costuma valer uma semana de retrabalho.
- **Discordar com argumento.** Se alguma decisão do esqueleto atrapalha o que
  vocês querem fazer, digam — várias dessas regras já mudaram por causa de um
  bom argumento. O que não vale é contornar em silêncio.
