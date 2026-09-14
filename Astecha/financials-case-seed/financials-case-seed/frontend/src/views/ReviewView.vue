<script setup>
// A TELA QUE DA VALOR AO APP — Sprint 2. Vale 15% da nota especifica.
//
// O que ela precisa fazer, na ordem de importancia:
//
//  1. DOCUMENTO AO LADO DO RASCUNHO. O analista tem que conferir sem trocar
//     de janela. Sem isso ele abre o PDF por fora e a tela vira digitacao.
//
//  2. DEIXAR CLARO O QUE A IA SUGERIU E O QUE O HUMANO CONFIRMOU. Sao dois
//     estados diferentes de confianca, e confundi-los e o que faz alguem
//     aprovar um numero que ninguem olhou.
//
//  3. ORDENAR PELA CONFIANCA, NAO PELA ORDEM DO PDF. O revisor deve comecar
//     pelo que a maquina menos sabe. Uma lista na ordem do papel obriga a
//     olhar as 40 linhas faceis antes das 3 dificeis.
//
//  4. CHECKS CONTABEIS AO VIVO. Corrigiu uma linha, o "Ativo = Passivo + PL"
//     recalcula na hora. E o feedback que transforma revisao em conferencia.
//
//  5. APROVAR = POST /extractions/{id}/approve, que monta o payload de
//     /statements/write. Botao desabilitado enquanto houver linha sem conta.
//
// Um conselho de escopo: NAO comece pelo bonito. Uma tabela feia com esses
// cinco comportamentos vale mais nota do que uma tela linda que so lista.
</script>

<template>
  <section>
    <h1 class="mb-1 text-xl font-semibold">Revisão da extração</h1>
    <p class="mb-6 text-sm text-slate-600">
      Confira o rascunho contra o documento, corrija o de-para e aprove.
    </p>

    <div
      class="rounded border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500"
    >
      Sprint 2 — a implementar. Leia os comentários no topo deste arquivo:
      eles são os critérios pelos quais esta tela é avaliada.
    </div>
  </section>
</template>
