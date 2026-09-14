<script setup>
import { onMounted, ref } from 'vue'

import financialsApi, { extractErrorMessage } from '@/services/financialsApi'

const documents = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await financialsApi.get('/documents')
    documents.value = data.results
  } catch (e) {
    error.value = extractErrorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section>
    <h1 class="mb-1 text-xl font-semibold">Documentos</h1>
    <p class="mb-6 text-sm text-slate-600">
      PDFs e planilhas brutos enviados por empresa, com o status do
      processamento.
    </p>

    <p v-if="loading" class="text-sm text-slate-500">Carregando…</p>
    <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-else-if="!documents.length" class="text-sm text-slate-500">
      Nenhum documento enviado.
    </p>

    <table v-else class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-slate-300 text-left">
          <th class="py-2 pr-4">Arquivo</th>
          <th class="py-2 pr-4">Tipo</th>
          <th class="py-2 pr-4">Enviado em</th>
          <th class="py-2">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in documents" :key="d.ID" class="border-b border-slate-100">
          <td class="py-1.5 pr-4">{{ d.ORIGINAL_FILENAME }}</td>
          <td class="py-1.5 pr-4 text-slate-600">{{ d.FILE_TYPE }}</td>
          <td class="py-1.5 pr-4 text-slate-600">{{ d.UPLOAD_DATE }}</td>
          <td class="py-1.5 text-slate-600">{{ d.PROCESSING_STATUS }}</td>
        </tr>
      </tbody>
    </table>

    <!--
      TODO Sprint 1/2:
        1. Campo de upload (multipart) -> POST /documents/upload
        2. Botao "Extrair" -> POST /documents/{id}/extract, que responde 202.
           A resposta NAO traz o resultado: traz um task_id. A tela precisa
           consultar o status periodicamente e so entao levar o usuario para a
           revisao. Um botao que trava a tela esperando a extracao acabar e o
           erro classico aqui — o PDF escaneado leva minutos.
        3. Estado FAILED tem que ser visivel e ter "tentar de novo". Documento
           preso em PARSING para sempre e a reclamacao numero 1 de quem opera.
    -->
  </section>
</template>
