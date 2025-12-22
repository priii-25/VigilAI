import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),

  register: (email: string, password: string, full_name: string) =>
    apiClient.post('/auth/register', { email, password, full_name }),
};

// Competitors API
export const competitorsAPI = {
  list: () => apiClient.get('/competitors/'),

  get: (id: number) => apiClient.get(`/competitors/${id}`),

  create: (data: any) => apiClient.post('/competitors/', data),

  delete: (id: number) => apiClient.delete(`/competitors/${id}`),

  triggerScrape: (id: number) => apiClient.post(`/competitors/${id}/scrape`),

  getUpdates: (id: number) => apiClient.get(`/competitors/${id}/updates`),

  news: (id: number) => apiClient.get(`/competitors/${id}/news`),
};

// Battlecards API
export const battlecardsAPI = {
  list: () => apiClient.get('/battlecards/'),

  update: (id: number, data: any) => apiClient.put(`/battlecards/${id}`, data),

  get: (id: number) => apiClient.get(`/battlecards/${id}`),

  create: (data: any) => apiClient.post('/battlecards/', data),

  delete: (id: number) => apiClient.delete(`/battlecards/${id}`),

  duplicate: (id: number) => apiClient.post(`/battlecards/${id}/duplicate`),

  getByCompetitor: (competitorId: number) =>
    apiClient.get(`/battlecards/competitor/${competitorId}`),

  publish: (id: number) => apiClient.post(`/battlecards/${id}/publish`),
};

// Logs API
export const logsAPI = {
  analyze: (logs: string[], source: string) =>
    apiClient.post('/logs/analyze', { logs, source }),

  getAnalysis: () => apiClient.get('/logs/analysis'),

  chat: (data: { message: string; anomaly_id?: string }) =>
    apiClient.post('/logs/chat', data),

  listAnomalies: (limit: number = 50) =>
    apiClient.get(`/logs/anomalies?limit=${limit}`),

  listIncidents: (status?: string) =>
    apiClient.get('/logs/incidents', { params: { status } }),

  resolveIncident: (id: number, resolution: string) =>
    apiClient.post(`/logs/incidents/${id}/resolve`, { resolution }),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => apiClient.get('/dashboard/stats'),

  getRecentActivity: (limit: number = 20) =>
    apiClient.get(`/dashboard/recent-activity?limit=${limit}`),
};

// Analytics API
export const analyticsAPI = {
  getMetrics: () => apiClient.get('/analytics/metrics'),

  getBattlecardUsage: () => apiClient.get('/analytics/battlecard-usage'),

  getWinRates: () => apiClient.get('/analytics/win-rates'),

  getImpactScores: () => apiClient.get('/analytics/impact-scores'),

  getLandscape: () => apiClient.get('/analytics/landscape'),

  getStrategyDrift: (competitorId: number) =>
    apiClient.get(`/analytics/strategy-drift/${competitorId}`),

  runSimulation: (data: { competitor_name: string; scenario: string; context?: string }) =>
    apiClient.post('/analytics/simulation', data),
};

export default apiClient;
