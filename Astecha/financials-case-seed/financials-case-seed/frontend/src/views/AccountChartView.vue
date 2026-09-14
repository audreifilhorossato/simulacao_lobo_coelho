<script setup>
import { onMounted, ref } from 'vue'

import financialsApi, { extractErrorMessage } from '@/services/financialsApi'

// Tela de referencia: e a unica ja ligada de ponta a ponta. Use-a como modelo
// (estados de carregando / erro / vazio) para as outras — uma tela que so
// funciona no caminho feliz nao conta como pronta.
const accounts = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await financialsApi.get('/account-chart', {
      params: { page_size: 500 },
    })
    accounts.value = data.results
  } catch (e) {
    error.value = extractErrorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section>
    <h1 class="mb-1 text-xl font-semibold">Plano de Contas</h1>
    <p class="mb-6 text-sm text-slate-600">
      Taxonomia única em que toda linha de balanço e de DRE é mapeada. Contas
      <code>STANDARD</code> não podem ser alteradas.
    </p>

    <p v-if="loading" class="text-sm text-slate-500">Carregando…</p>
    <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-else-if="!accounts.length" class="text-sm text-slate-500">
      Nenhuma conta. A migration 0002 rodou?
    </p>

    <table v-else class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-slate-300 text-left">
          <th class="py-2 pr-4">Código</th>
          <th class="py-2 pr-4">Conta</th>
          <th class="py-2 pr-4">Tipo</th>
          <th class="py-2 pr-4">Demonstração</th>
          <th class="py-2">Origem</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="a in accounts"
          :key="a.ACCOUNT_CODE"
          class="border-b border-slate-100"
        >
          <td class="py-1.5 pr-4 font-mono text-xs">{{ a.ACCOUNT_CODE }}</td>
          <td
            class="py-1.5 pr-4"
            :style="{ paddingLeft: `${(a.LEVEL - 1) * 16}px` }"
          >
            {{ a.ACCOUNT_NAME }}
          </td>
          <td class="py-1.5 pr-4 text-slate-600">{{ a.ACCOUNT_TYPE }}</td>
          <td class="py-1.5 pr-4 text-slate-600">{{ a.STATEMENT }}</td>
          <td class="py-1.5 text-slate-600">{{ a.ORIGIN }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
