# Arreio de avaliação

O número que vale **30% da nota específica**.

```bash
python eval/run.py --provider naive       # o piso: 0% em tudo
python eval/run.py --provider rule_based  # Sprint 1
python eval/run.py --provider llm         # Sprint 3
python eval/run.py --case bp-duas-colunas # um caso, com o detalhe dos erros
python eval/run.py --markdown             # saida para o resumo do CI
```

## Por que ele existe

Sem uma medida, "melhorou" é opinião. Com ela, a evolução do projeto vira três
números comparáveis — e esses três números, lado a lado, são a sua apresentação
final:

| Sprint | Provider | SCORE esperado |
|---|---|---|
| 0 | `naive` | 0% (o piso, verificado) |
| 1 | `rule_based` | o seu primeiro número de verdade |
| 3 | `llm` | tem que superar o anterior — ou a IA não valeu a pena |

Se `rule_based` empatar com `naive`, o defeito está no arreio, não no provider:
o `naive` existe justamente como controle.

## O que é medido

| Métrica | O que pega | Peso |
|---|---|---|
| `DOC_OK` | número certo de demonstrações. Um balanço de duas colunas são **duas**. | 10% |
| `PERIODO` | a competência bate. Errar grava o balanço no ano errado. | 15% |
| `ESCALA` | o `scale_factor` bate. É o erro de **1000×**. | 15% |
| `CONTA_REC` | recall do de-para: das linhas do gabarito, quantas você achou e mapeou certo. | 25% |
| `CONTA_PREC` | precisão: das linhas que você entregou, quantas estavam certas. | 15% |
| `VALOR` | das linhas com conta certa, quantas têm o valor certo. | 20% |

**Recall alto com precisão baixa não é sucesso**: significa que o provider está
chutando conta, e o analista tem que revisar tudo do mesmo jeito — que é o
trabalho que o app existe para eliminar.

## Os três casos

| Caso | O que ele cobra |
|---|---|
| `bp-simples` | O básico: uma coluna, valores em reais. Se você não acerta este, não adianta ir aos outros. |
| `dre-milhares-parenteses` | Escala (`R$ mil`), parênteses = negativo, deduções da receita (a exceção de sinal), subtotais impressos, e uma linha que **não** é conta ("Lucro por ação"). |
| `bp-duas-colunas` | Um documento, **duas** demonstrações. E o mesmo rótulo ("Empréstimos e financiamentos") em dois blocos diferentes — o que prova que um dicionário rótulo→conta não basta. |

Cada `expected.json` tem um bloco `_comentario` explicando a armadilha. Leia
antes de programar; economiza dias.

## Como funciona por dentro

Cada caso tem dois arquivos:

- **`parsed.json`** — o documento **já parseado** (texto + tabelas). É a entrada
  do provider. Vem pronto para vocês medirem a extração **antes** de o parser
  existir — assim a Sprint 1 não fica bloqueada esperando o OCR.
- **`expected.json`** — o gabarito.

Quando o parser de vocês existir, gerem o `parsed.json` a partir dele: aí o
número passa a medir o pipeline inteiro, e não só a extração.

## A regra de ouro

**Não edite `expected.json` para o seu provider passar.**

Se você achar que o gabarito está errado, abra uma issue mostrando por quê —
isso conta a favor, e já aconteceu de o gabarito estar errado mesmo. Ajustar o
gabarito para caber no código é a única coisa que zera o critério inteiro.

## O conjunto oculto

A avaliação final roda contra um **segundo conjunto de documentos**, que vocês
não recebem. Ele tem as mesmas armadilhas em documentos diferentes.

Consequência prática: **não vale codificar o gabarito.** Um `if "Caixa e
equivalentes de caixa" in label: return "1.01.01"` acerta 100% aqui e 0% lá. O
que generaliza é normalizar o rótulo, casar por similaridade, usar o bloco em
que a linha está e conferir contra a equação contábil — não decorar.

## Acrescentando casos

Casos novos são bem-vindos e contam como trabalho:

1. `mkdir eval/cases/<slug>`
2. `parsed.json` — texto e tabelas do documento
3. `expected.json` — o gabarito, com `_comentario` dizendo qual sujeira ele cobre
4. Rode `python eval/run.py --case <slug>` e confira que o gabarito fecha
   (balanço bate, DRE fecha) antes de commitar
