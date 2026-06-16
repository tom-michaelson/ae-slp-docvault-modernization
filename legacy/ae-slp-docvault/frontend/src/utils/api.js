import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach auth token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('docvault_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — basic error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('Unauthorized — token may be expired');
    }
    return Promise.reject(error);
  }
);

// API methods
export const fetchDocuments = () => api.get('/documents');
export const fetchDocument = (id) => api.get(`/documents/${id}`);
export const uploadDocument = (formData) =>
  api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const updateTags = (id, tags) => api.put(`/documents/${id}/tags`, { tags });
export const fetchTags = (id) => api.get(`/documents/${id}/tags`);
export const searchDocuments = (query) => api.get(`/search?q=${encodeURIComponent(query)}`);
export const getPreviewUrl = (id) => `${API_BASE_URL}/documents/${id}/preview`;
export const checkHealth = () => api.get('/health');

export default api;
