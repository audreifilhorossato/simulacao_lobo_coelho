import axios from 'axios'

// Espelha `frontend/src/services/financialsApi.js` da plataforma Astecha.
//
// Duas coisas nao sao detalhe:
//  - baseURL RELATIVA. Host fixo aqui quebra na migracao.
//  - SEM barra no fim do caminho. O router do DRF esta com
//    `trailing_slash=False`; um POST em `/companies/` recebe 301 e o CORPO E
//    DESCARTADO — a escrita "some" sem erro nenhum.
const financialsApi = axios.create({
  baseURL: '/api/v1/credit/financials',
  timeout: 60_000,
})

export function extractErrorMessage(error) {
  const data = error?.response?.data
  if (!data) return error?.message || 'Erro de comunicacao com o servidor'
  if (Array.isArray(data)) return data.join(', ')
  if (typeof data === 'object') {
    const fieldErrors = Object.values(data).flat().filter(Boolean)
    if (fieldErrors.length) return fieldErrors.join(', ')
  }
  return data.detail || data.error || data.message || JSON.stringify(data)
}

export default financialsApi
