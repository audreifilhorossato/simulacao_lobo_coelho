import { createRouter, createWebHistory } from 'vue-router'

// Os caminhos espelham os da plataforma Astecha
// (/private-data/credit/financials/...). Manter isso torna a migracao da tela
// um copiar de arquivos; mudar so faz voce reescrever depois.
const routes = [
  { path: '/', redirect: '/credit/financials/companies' },
  {
    path: '/credit/financials/companies',
    name: 'FinancialsCompanies',
    component: () => import('@/views/CompaniesView.vue'),
  },
  {
    path: '/credit/financials/account-chart',
    name: 'FinancialsAccountChart',
    component: () => import('@/views/AccountChartView.vue'),
  },
  {
    path: '/credit/financials/documents',
    name: 'FinancialsDocuments',
    component: () => import('@/views/DocumentsView.vue'),
  },
  {
    path: '/credit/financials/statements',
    name: 'FinancialsStatements',
    component: () => import('@/views/StatementsView.vue'),
  },
  // Sprint 2 — a tela que da valor ao app. Ver o TODO em ReviewView.vue.
  {
    path: '/credit/financials/review/:extractionId?',
    name: 'FinancialsReview',
    component: () => import('@/views/ReviewView.vue'),
  },
]

export default createRouter({ history: createWebHistory(), routes })
