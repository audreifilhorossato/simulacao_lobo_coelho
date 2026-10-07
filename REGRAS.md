# Regras da simulação

Este documento descreve como o ecossistema funciona: o que existe no mundo, o que acontece a cada tick e como cada espécie decide o que fazer. Os valores citados são os padrões do código; a maioria está em [`dominio/Tipos.h`](../simulacao_lobo_coelho/dominio/Tipos.h).

## O mundo

- O mundo é uma grade de **80 × 80 células**.
- A grade é **toroidal**: as bordas se conectam. Sair por um lado leva ao lado oposto, tanto na movimentação quanto na visão.
- Cada célula pode conter, ao mesmo tempo:
  - no máximo **um animal**;
  - no máximo **uma carcaça**;
  - uma **planta** (ou não).
- O tempo avança em **ticks**. Por padrão, um tick equivale a 0,1 s, ou seja, 10 ticks por segundo.

## População inicial

No início, a simulação sorteia uma quantidade de animais entre **0,5% e 1% das células** (de 32 a 64 numa grade 80 × 80). As espécies se alternam (coelho, lobo, coelho, lobo...), então a população começa dividida ao meio. Cada animal recebe uma posição aleatória; se a posição sorteada já estiver ocupada, aquele animal simplesmente não é criado.

| | Coelho | Lobo |
|---|---|---|
| Energia inicial | 100 | 200 |

## Parâmetros das espécies

| Parâmetro | Coelho | Lobo |
|---|---|---|
| Energia máxima | 200 | 300 |
| Custo de energia por tick (só por estar vivo) | 1 | 1 |
| Custo de energia por movimento | 1 | 2 |
| Custo de energia para reproduzir | 15 | 50 |
| Raio de visão | 5 | 7 |
| Idade máxima (ticks) | 75 | 130 |
| Idade mínima para reproduzir (ticks) | 10 | 30 |

| Alimento | Energia que fornece |
|---|---|
| Planta (comida por coelho) | 40 |
| Carcaça (comida por lobo) | 60 |

A energia nunca passa do máximo da espécie: o que excede ao comer é descartado.

## Ordem dos eventos em um tick

A cada tick, a simulação executa estas etapas, sempre nesta ordem:

1. **Mortes.** Todo animal que foi atacado no tick anterior, que passou da idade máxima ou cuja energia chegou a zero (ou menos) é retirado do mundo.
2. **Carcaças novas.** Cada animal que morreu deixa uma carcaça na sua célula, guardando a energia que tinha ao morrer. Se a célula já tiver uma carcaça, nenhuma nova é criada.
3. **Carcaças velhas.** Somem as carcaças com **50 ticks ou mais** e as que guardam energia zero ou negativa.
4. **Custo de viver.** Cada animal vivo perde sua energia por tick.
5. **Decisões.** Cada animal vivo olha ao redor e escolhe uma ação. Todos decidem olhando o mesmo estado do mundo, como se fosse ao mesmo tempo.
6. **Conflitos.** Quando dois ou mais animais escolhem a mesma célula de destino, a simulação decide quem vai (veja abaixo).
7. **Ações.** As ações aprovadas são executadas, ataques primeiro.
8. **Plantas novas.** Cada célula que ainda não tem planta tem **0,15% de chance** de ganhar uma. Numa grade 80 × 80, isso dá em média cerca de 10 plantas novas por tick.

Consequências dessa ordem que valem a pena saber:

- Um coelho atacado continua no tabuleiro até o começo do tick seguinte, quando vira carcaça.
- Um animal que morre de fome guarda energia zero ou negativa, então a carcaça dele é criada e removida no mesmo tick. Na prática, **só deixam carcaça visível os animais mortos por ataque ou por idade**.
- O lobo ganha sempre 60 de energia ao comer uma carcaça, independentemente da energia que ela guarda.

## Visão

Cada animal enxerga as células dentro de um **círculo** com o raio de visão da sua espécie (contando a grade toroidal). Para cada célula visível, ele sabe se há planta, carcaça ou animal, e de qual espécie.

## Ações possíveis

| Ação | Efeito |
|---|---|
| **Esperar** | Não faz nada. |
| **Mover** | Vai para uma das 8 células vizinhas, se estiver livre. Paga o custo de movimento. Animais mais novos que a idade mínima de reprodução se movem sem custo. |
| **Comer** | Coelho come a planta da própria célula; lobo come a carcaça da própria célula. |
| **Reproduzir** | Cria um filhote numa célula vizinha livre. O filhote nasce com **metade da energia** do pai, e o pai paga o custo de reprodução. Se o pai tiver menos energia que o custo, nada acontece. Se a célula escolhida tiver sido ocupada nesse meio-tempo, o filhote não nasce, mas o pai paga o custo mesmo assim. |
| **Matar** | O lobo ataca um coelho numa célula vizinha. O coelho morre no início do tick seguinte. |

## Como o coelho decide

1. **Se está sobre uma planta, come.**
2. Calcula um **vetor de direção** somando a influência de tudo o que vê. Cada influência é mais forte quanto mais perto, proporcional a 1/distância²:
   - plantas **atraem** (peso 1);
   - carcaças **repelem** (peso 1);
   - lobos **repelem com força dobrada** (peso 2).
3. Lista as células vizinhas livres. Se não há nenhuma, **espera**.
4. Com cerca de **20% de chance**, se tiver energia acima de 50 e idade mínima, **reproduz** numa vizinha livre aleatória.
5. Se o vetor de direção é nulo (nada interessante à vista), **vaga**: com cerca de 60% de chance move para uma vizinha livre aleatória, senão espera.
6. Caso contrário, **move** para a vizinha livre cuja direção mais se aproxima do vetor.

## Como o lobo decide

1. **Se está sobre uma carcaça, come.**
2. Calcula o **vetor de direção**:
   - carcaças **atraem com força tripla** (peso 3);
   - coelhos **atraem** (peso 1).

   Coelhos nas células vizinhas viram **alvos possíveis**.
3. Lista as vizinhas para onde pode ir: as livres e as que têm carcaça. Se não há nenhuma, **espera**.
4. Se há alvos, com cerca de **70% de chance** **ataca** um deles, sorteado.
5. Com cerca de **3% de chance**, se tiver energia acima de 50 e idade mínima, **reproduz**.
6. Se o vetor de direção é nulo, **vaga** como o coelho (60% move, senão espera).
7. Caso contrário, **move** na direção do vetor.

As porcentagens das etapas 4 e 5 (e do vagar) vêm de **um único sorteio** de 0 a 100 por animal por tick, então elas não são independentes entre si. Por exemplo, um coelho que tirou um valor alto o suficiente para reproduzir, mas não tinha energia, nunca vai vagar por movimento aleatório naquele tick.

## Conflitos

Depois que todos decidem, as ações são agrupadas pela **célula de destino**:

- **Ataques** são todos aprovados e executados antes de qualquer outra ação.
- **Esperar** e **Comer** têm como destino a célula do próprio animal e são aprovados.
- Quando vários animais querem **mover para** (ou **reproduzir em**) a mesma célula, vence o que tem **mais energia**. Se houver empate entre os mais fortes, ninguém vai.

## Aleatoriedade e reprodutibilidade

Toda a aleatoriedade vem de geradores `std::mt19937` derivados da semente `semente_base` (padrão 1). Nas decisões, cada animal recebe em cada tick um gerador próprio, criado a partir de `(semente, tick, id do animal)`. Assim, as decisões não dependem da ordem em que os animais são processados nem de quantas threads são usadas. Os detalhes estão em [ARQUITETURA.md](ARQUITETURA.md#paralelismo-e-determinismo).
