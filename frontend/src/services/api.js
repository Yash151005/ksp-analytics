import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL;

if (!API_BASE_URL) {
  throw new Error('VITE_API_URL is not defined');
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => 
    api.post('/auth/login', { username, password }),
  refresh: () => 
    api.post('/auth/refresh'),
};

export const crimesAPI = {
  list: (params) => 
    api.get('/crimes', { params }),
  get: (id) => 
    api.get(`/crimes/${id}`),
  getSummary: (days) => 
    api.get('/crimes/stats/summary', { params: { days } }),
  getByDistrict: (days) => 
    api.get('/crimes/stats/by-district', { params: { days } }),
  getByType: (days) => 
    api.get('/crimes/stats/by-type', { params: { days } }),
  getTrend: (months) => 
    api.get('/crimes/stats/trend', { params: { months } }),
  getHotspots: () => 
    api.get('/crimes/hotspots'),
  exportCSV: (params) => 
    api.get('/crimes/export/csv', { params }),
};

export const criminalsAPI = {
  list: (params) => 
    api.get('/criminals', { params }),
  get: (id) => 
    api.get(`/criminals/${id}`),
  getAssociates: (id) => 
    api.get(`/criminals/${id}/associates`),
  getNetwork: () => 
    api.get('/criminals/network/data'),
  getStats: () => 
    api.get('/criminals/stats/summary'),
  getHighRisk: () => 
    api.get('/criminals/high-risk'),
  exportCSV: (params) => 
    api.get('/criminals/export/csv', { params }),
};

export const analyticsAPI = {
  getTemporalHeatmap: () => 
    api.get('/analytics/temporal-heatmap'),
  getAnomalies: (sensitivity) => 
    api.get('/analytics/anomalies', { params: { sensitivity } }),
  getRepeatOffenders: (minCrimes) => 
    api.get('/analytics/repeat-offenders', { params: { min_crimes: minCrimes } }),
  getRiskScores: () => 
    api.get('/analytics/risk-scores'),
  getHotspotsMap: () => 
    api.get('/analytics/hotspots-map'),
  getDemographics: () => 
    api.get('/analytics/demographics'),
  getReportSnapshot: (params) => 
    api.post('/analytics/report-snapshot', params),
};

export const alertsAPI = {
  list: (params) => 
    api.get('/alerts', { params }),
  get: (id) => 
    api.get(`/alerts/${id}`),
  acknowledge: (id) => 
    api.post(`/alerts/${id}/acknowledge`),
  escalate: (id) => 
    api.post(`/alerts/${id}/escalate`),
  getSummary: () => 
    api.get('/alerts/stats/summary'),
  getBySeverity: (days) => 
    api.get('/alerts/by-severity', { params: { days } }),
  getActive: () => 
    api.get('/alerts/active'),
  exportCSV: (params) => 
    api.get('/alerts/export/csv', { params }),
};

export const reportsAPI = {
  list: (params) => 
    api.get('/reports', { params }),
  get: (id) => 
    api.get(`/reports/${id}`),
  update: (id, data) => 
    api.put(`/reports/${id}`, data),
  delete: (id) => 
    api.delete(`/reports/${id}`),
  getTemplates: () => 
    api.get('/reports/templates'),
  generate: (data) => 
    api.post('/reports/generate', data),
  export: (id, format) => 
    api.post(`/reports/${id}/export`, { format }, { responseType: 'blob' }),
  getSnapshot: (params) => 
    api.get('/reports/snapshot/data', { params }),
};

export const aiAPI = {
  streamRequest: async (endpoint, onChunk, onError) => {
    let reader = null;
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream'
      };
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
      });

      // Handle both 200 OK and streaming responses
      if (!response.ok && response.status !== 200) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error(`Response body is empty (status ${response.status})`);
      }

      reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let done = false;

      while (!done) {
        const { done: streamDone, value } = await reader.read();
        done = streamDone;

        if (value) {
          buffer += decoder.decode(value, { stream: true });
        }

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('data: ')) {
            const jsonStr = trimmedLine.slice(6).trim();
            if (jsonStr === '[DONE]') {
              done = true;
              break;
            }
            if (jsonStr) {
              try {
                const data = JSON.parse(jsonStr);
                if (data.error) {
                  if (onError) onError(new Error(data.error));
                  return;
                }
                if (data.content) {
                  onChunk(data.content);
                }
              } catch (e) {
                console.warn('Failed to parse JSON:', jsonStr, e);
              }
            }
          }
        }
      }

      // Handle any remaining buffer
      if (buffer.trim()) {
        const trimmedLine = buffer.trim();
        if (trimmedLine.startsWith('data: ')) {
          const jsonStr = trimmedLine.slice(6).trim();
          if (jsonStr && jsonStr !== '[DONE]') {
            try {
              const data = JSON.parse(jsonStr);
              if (data.content) {
                onChunk(data.content);
              }
            } catch (e) {
              console.warn('Failed to parse final JSON:', jsonStr, e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream error:', error);
      if (reader) {
        try {
          reader.cancel();
        } catch (e) {
          // Ignore cancel errors
        }
      }
      if (onError) onError(error);
      else throw error;
    }
  },

  getBriefing: (onChunk, onError) =>
    aiAPI.streamRequest('/ai/briefing', onChunk, onError),
  analyzeNetwork: (onChunk, onError) =>
    aiAPI.streamRequest('/ai/analyze-network', onChunk, onError),
  generateProfile: (criminalId, onChunk, onError) => {
    // For profile, we might need to pass criminal ID differently
    const endpoint = `/ai/profile/${criminalId}`;
    return aiAPI.streamRequest(endpoint, onChunk, onError);
  },
  detectHotspots: (onChunk, onError) =>
    aiAPI.streamRequest('/ai/hotspots', onChunk, onError),
  forecast: async (days, onChunk, onError) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/ai/forecast`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ days })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      if (!response.body) throw new Error('Response body is empty');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6).trim();
            if (jsonStr && jsonStr !== '[DONE]') {
              try {
                const data = JSON.parse(jsonStr);
                if (data.content) onChunk(data.content);
              } catch (e) {
                // Ignore JSON parse errors
              }
            }
          }
        }
      }
    } catch (error) {
      if (onError) onError(error);
      else throw error;
    }
  },
  explainAnomaly: async (data, onChunk, onError) => {
    let reader = null;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/ai/anomaly-explanation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      if (!response.body) {
        throw new Error(`Response body is empty (status ${response.status})`);
      }

      reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        if (value) {
          buffer += decoder.decode(value, { stream: true });
        }

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('data: ')) {
            const jsonStr = trimmedLine.slice(6).trim();
            if (jsonStr === '[DONE]') return;
            if (jsonStr) {
              try {
                const parsed = JSON.parse(jsonStr);
                if (parsed.error) {
                  if (onError) onError(new Error(parsed.error));
                  return;
                }
                if (parsed.content) onChunk(parsed.content);
              } catch (e) {
                console.warn('Failed to parse JSON:', jsonStr, e);
              }
            }
          }
        }
      }
    } catch (error) {
      if (onError) onError(error);
      else throw error;
    } finally {
      if (reader) {
        try {
          reader.cancel();
        } catch (e) {
          // Ignore cancel errors
        }
      }
    }
  },
  getAlertRecommendation: (data) => 
    api.post('/ai/alert-recommendation', data),
  generateReportNarrative: (data) => 
    api.post('/ai/report-narrative', data),
  getStatus: () => 
    api.get('/ai/status'),
};

export const adminAPI = {
  listUsers: (params) => 
    api.get('/admin/users', { params }),
  getUser: (id) => 
    api.get(`/admin/users/${id}`),
  createUser: (data) => 
    api.post('/admin/users', data),
  updateUser: (id, data) => 
    api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => 
    api.delete(`/admin/users/${id}`),
  getPermissions: () => 
    api.get('/admin/permissions'),
  listAuditLogs: (params) => 
    api.get('/admin/audit-logs', { params }),
  getAuditStats: (days) => 
    api.get('/admin/audit-logs/stats', { params: { days } }),
  getSystemHealth: () => 
    api.get('/admin/system-health'),
};

export default api;
