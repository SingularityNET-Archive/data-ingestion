/** API service for communicating with the backend dashboard API. */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const kpisApi = {
  getKPIs: () => api.get('/api/kpis'),
};

export const alertsApi = {
  list: (params) => api.get('/api/alerts', { params }),
  acknowledge: (alertId) => api.post(`/api/alerts/${alertId}/acknowledge`),
};

export const meetingsApi = {
  list: (params) => api.get('/api/meetings', { params }),
  getDetail: (id) => api.get(`/api/meetings/${id}`),
};

export const exportsApi = {
  export: (data) => api.post('/api/exports', data, { responseType: 'blob' }),
};

export const runsApi = {
  list: (params) => api.get('/api/runs', { params }),
  getMonthly: (params) => api.get('/api/runs/monthly', { params }),
};

export default api;

