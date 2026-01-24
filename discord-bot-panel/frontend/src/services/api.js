import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default {
  // Contacts
  getContacts: () => client.get('/contacts/'),
  createContact: (data) => client.post('/contacts/', data),
  deleteContact: (id) => client.delete(`/contacts/${id}`),

  // Files
  getFiles: () => client.get('/files/'),
  uploadFile: (formData) => client.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteFile: (id) => client.delete(`/files/${id}`),

  // API Keys
  getKeys: () => client.get('/api-keys/'),
  createKey: (data) => client.post('/api-keys/', data),
  revokeKey: (id) => client.delete(`/api-keys/${id}`),

  // Stats & Logs
  getStats: () => client.get('/stats/'),
  getLogs: () => client.get('/stats/logs'),
  clearLogs: () => client.delete('/stats/logs'),

  // Google Auth
  connectGoogle: async () => {
    try {
      const response = await client.get('/auth/google/connect');
      const url = response.data.url;

      if (window.pywebview) {
        window.pywebview.api.open_external(url);
      } else {
        window.location.href = url;
      }
    } catch (error) {
      console.error("Failed to initiate Google connection", error);
    }
  },
  getGoogleStatus: () => client.get('/auth/google/status'),
  disconnectGoogle: () => client.delete('/auth/google/disconnect'),

  // Discord Auth (System Browser)
  initiateDiscordLogin: () => client.get('/auth/discord/login?user_redirect=true'),
  pollDiscordLogin: (state) => client.get(`/auth/discord/poll?state=${state}`),

  // Setup
  getSetupStatus: () => client.get('/setup/status'),
  saveSetupConfig: (data) => client.post('/setup/config', data),
};
