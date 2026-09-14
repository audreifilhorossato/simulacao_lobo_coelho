<script setup>
import { onMounted, ref } from 'vue'

import financialsApi, { extractErrorMessage } from '@/services/financialsApi'

const statements = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await financialsApi.get('/statements')
    statements.value = data.results
  } catch (e) {
    error.value = extractErrorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section>
    <h1 class="mb-1 text-xl font-semibold">Demonstrações</h1>
    <p class="mb-6 text-sm text-slate-600">
      Balanços e DREs já padronizados — comparáveis entre empresas e no tempo.
    </p>

    <p v-if="loading" class="text-sm text-slate-500">Carregando…</p>
    <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-else-if="!statements.length" class="text-sm text-slate-500">
      Nenhuma demonstração gravada.
    </p>

    <table v-else class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-slate-300 text-left">
          <th class="py-2 pr-4">Empresa</th>
          <th class="py-2 pr-4">Tipo</th>
          <th class="py-2 pr-4">Competência</th>
          <th class="py-2 pr-4">Linhas</th>
          <th class="py-2">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in statements" :key="s.ID" class="border-b border-slate-100">
          <td class="py-1.5 pr-4">{{ s.COMPANY }}</td>
          <td class="py-1.5 pr-4 text-slate-600">{{ s.STATEMENT_TYPE }}</td>
          <td class="py-1.5 pr-4">{{ s.PERIOD_END_DATE }}</td>
          <td class="py-1.5 pr-4 text-slate-600">{{ s.LINES?.length ?? 0 }}</td>
          <td class="py-1.5 text-slate-600">{{ s.STATUS }}</td>
        </tr>
      </tbody>
    </table>

    <!--
      TODO Sprint 4 — indices e covenants:
        - GET /indicators?company_id=&period=  (liquidez, alavancagem, cobertura)
        - GET /indicators/compare              (a comparabilidade, que e o
          objetivo de negocio inteiro: sem ela, padronizar nao serviu para nada)
        - GET /covenant-checks?company_id=     (CUMPRIDO / DESCUMPRIDO / SEM_DADO)
    -->
  </section>
</template>
