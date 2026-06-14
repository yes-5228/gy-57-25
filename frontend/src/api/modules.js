import { api } from './client'

export const dashboardApi = {
  summary: () => api.get('/dashboard/summary'),
  lessonStats: () => api.get('/dashboard/lesson-stats'),
}

export const studentApi = {
  list: (params) => api.get('/students', { params }),
  create: (payload) => api.post('/students', payload),
  get: (id) => api.get(`/students/${id}`),
  updateTags: (id, tags) => api.patch(`/students/${id}/tags`, { tags }),
  listTagDefinitions: () => api.get('/students/tags/definitions'),
  getAppointmentHints: (id) => api.get(`/students/${id}/appointment-hints`),
}

export const coachApi = {
  list: () => api.get('/coaches'),
  create: (payload) => api.post('/coaches', payload),
  setActive: (id, active) => api.patch(`/coaches/${id}/active?active=${active}`, {}),
}

export const appointmentApi = {
  list: () => api.get('/appointments'),
  create: (payload) => api.post('/appointments', payload),
  cancel: (id, reason) => api.post(`/appointments/${id}/cancel`, { reason }),
}
