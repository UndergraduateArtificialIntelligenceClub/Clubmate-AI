import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
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
  connectGoogle: () => window.location.href = `${API_URL}/auth/google/connect`,
  getGoogleStatus: () => client.get('/auth/google/status'),
  disconnectGoogle: () => client.delete('/auth/google/disconnect'),
};
