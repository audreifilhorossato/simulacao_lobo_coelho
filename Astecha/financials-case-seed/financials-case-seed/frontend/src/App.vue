<script setup>
import { RouterLink, RouterView } from 'vue-router'

const nav = [
  { label: 'Empresas', to: '/credit/financials/companies' },
  { label: 'Plano de Contas', to: '/credit/financials/account-chart' },
  { label: 'Documentos', to: '/credit/financials/documents' },
  { label: 'Demonstrações', to: '/credit/financials/statements' },
  { label: 'Revisão', to: '/credit/financials/review' },
]
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
        <span class="font-semibold">Financials</span>
        <nav class="flex gap-4 text-sm">
          <RouterLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="text-slate-600 hover:text-slate-900"
            active-class="font-medium text-slate-900"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-6 py-8">
      <RouterView />
    </main>
  </div>
</template>
