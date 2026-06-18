/**
 * API Client (DUPLICATE of src/utils/api.js)
 * 
 * This file exists in src/lib/ as a different API call wrapper
 * than src/utils/api.js. Different base URL handling, different
 * error handling, different interceptor logic.
 * Constitution Principle V — duplicate utility directories.
 */

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

/**
 * Generic fetch wrapper (uses native fetch instead of axios like utils/api.js)
 */
async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Add auth token if available
  const token = localStorage.getItem('docvault_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Request failed: ${response.status}`);
  }
  
  return response.json();
}

// API methods (different naming conventions than utils/api.js)
export const getDocuments = () => request('/documents');
export const getDocument = (id) => request(`/documents/${id}`);
export const createDocument = (formData) =>
  fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
    headers: {
      Authorization: `Bearer ${localStorage.getItem('docvault_token') || ''}`,
    },
  }).then((r) => r.json());

export const setTags = (id, tags) =>
  request(`/documents/${id}/tags`, {
    method: 'PUT',
    body: JSON.stringify({ tags }),
  });

export const searchDocs = (query) => request(`/search?q=${encodeURIComponent(query)}`);

export default request;
