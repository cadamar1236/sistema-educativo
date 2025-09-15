/**
 * Configuración de la API para el frontend
 */

// URL base del backend
export const API_BASE_URL = 'http://127.0.0.1:8000'

/**
 * Función helper para hacer llamadas a la API
 */
export const apiCall = async (endpoint: string, options?: RequestInit) => {
  const url = `${API_BASE_URL}${endpoint}`
  
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
}

/**
 * Función helper para endpoints de agentes
 */
export const agentsApi = {
  status: () => apiCall('/api/agents/status'),
  chat: (data: any) => apiCall('/api/agents/unified-chat', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
}

export default apiCall
