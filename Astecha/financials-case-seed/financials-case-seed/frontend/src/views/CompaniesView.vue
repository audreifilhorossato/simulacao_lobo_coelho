<script setup>
import { onMounted, ref } from 'vue'

import financialsApi, { extractErrorMessage } from '@/services/financialsApi'

const companies = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await financialsApi.get('/companies')
    companies.value = data.results
  } catch (e) {
    error.value = extractErrorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section>
    <h1 class="mb-1 text-xl font-semibold">Empresas</h1>
    <p class="mb-6 text-sm text-slate-600">
      Contrapartes cujas demonstrações são padronizadas.
    </p>

    <p v-if="loading" class="text-sm text-slate-500">Carregando…</p>
    <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-else-if="!companies.length" class="text-sm text-slate-500">
      Nenhuma empresa cadastrada ainda.
    </p>

    <table v-else class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-slate-300 text-left">
          <th class="py-2 pr-4">Empresa</th>
          <th class="py-2 pr-4">CNPJ</th>
          <th class="py-2">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in companies" :key="c.ID" class="border-b border-slate-100">
          <td class="py-1.5 pr-4">{{ c.NAME }}</td>
          <td class="py-1.5 pr-4 font-mono text-xs">{{ c.CNPJ }}</td>
          <td class="py-1.5 text-slate-600">{{ c.STATUS }}</td>
        </tr>
      </tbody>
    </table>

    <!--
      TODO Sprint 1 — formulario de cadastro.
      Lembre: o POST vai para `/companies` SEM barra no fim.
    -->
  </section>
</template>
