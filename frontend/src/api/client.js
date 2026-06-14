const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

function buildQueryString(params) {
  if (!params) return ''
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ''
  )
  if (entries.length === 0) return ''
  return '?' + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&')
}

async function request(path, options = {}) {
  const query = options.params ? buildQueryString(options.params) : ''
  const response = await fetch(`${API_BASE}${path}${query}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    let message = await response.text()
    try {
      const parsed = JSON.parse(message)
      if (parsed && typeof parsed.detail === 'string') {
        message = parsed.detail
      }
    } catch (e) {
      // ignore JSON parse error
    }
    throw new Error(message || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  get: (path, options = {}) => request(path, { ...options, method: 'GET' }),
  post: (path, body, options = {}) =>
    request(path, { ...options, method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: (path, body, options = {}) =>
    request(path, { ...options, method: 'PATCH', body: body !== undefined ? JSON.stringify(body) : undefined }),
}
