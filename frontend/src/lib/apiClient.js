// API Client - ITEM 89: Centralized API client with fetch wrapper
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  // Get auth token from localStorage
  getAuthToken() {
    return localStorage.getItem('access_token');
  }

  // Set auth token in localStorage
  setAuthToken(token) {
    localStorage.setItem('access_token', token);
  }

  // Remove auth token from localStorage
  removeAuthToken() {
    localStorage.removeItem('access_token');
  }

  // Build headers with auth token
  buildHeaders(customHeaders = {}) {
    const headers = { ...this.defaultHeaders, ...customHeaders };
    const token = this.getAuthToken();

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  // Handle response
  async handleResponse(response) {
    const contentType = response.headers.get('content-type');
    const isJSON = contentType && contentType.includes('application/json');

    let data;
    if (isJSON) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      // Handle specific error statuses
      if (response.status === 401) {
        // Unauthorized - clear token and redirect to login
        this.removeAuthToken();
        window.location.href = '/login';
        throw new APIError('Unauthorized', 401, data);
      }

      if (response.status === 403) {
        toast.error('You do not have permission to perform this action');
        throw new APIError('Forbidden', 403, data);
      }

      if (response.status === 404) {
        throw new APIError('Resource not found', 404, data);
      }

      if (response.status === 422) {
        // Validation error
        const message = data.detail?.[0]?.msg || data.message || 'Validation error';
        toast.error(message);
        throw new APIError(message, 422, data);
      }

      if (response.status >= 500) {
        toast.error('Server error. Please try again later.');
        throw new APIError('Server error', response.status, data);
      }

      const errorMessage = data.message || data.detail || 'An error occurred';
      throw new APIError(errorMessage, response.status, data);
    }

    return data;
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: this.buildHeaders(options.headers),
    };

    try {
      const response = await fetch(url, config);
      return await this.handleResponse(response);
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      // Network error or other fetch errors
      console.error('API request failed:', error);
      toast.error('Network error. Please check your connection.');
      throw new APIError('Network error', 0, error);
    }
  }

  // GET request
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;

    return this.request(url, {
      method: 'GET',
    });
  }

  // POST request
  async post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options,
    });
  }

  // PUT request
  async put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options,
    });
  }

  // PATCH request
  async patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
      ...options,
    });
  }

  // DELETE request
  async delete(endpoint, options = {}) {
    return this.request(endpoint, {
      method: 'DELETE',
      ...options,
    });
  }

  // Upload file
  async upload(endpoint, formData, onProgress = null) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getAuthToken();

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
          }
        });
      }

      xhr.addEventListener('load', async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText);
          resolve(data);
        } else {
          const error = JSON.parse(xhr.responseText);
          reject(new APIError(error.message || 'Upload failed', xhr.status, error));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new APIError('Upload failed', 0, null));
      });

      xhr.open('POST', url);

      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.send(formData);
    });
  }

  // Download file
  async download(endpoint, filename) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = this.buildHeaders();

    try {
      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new APIError('Download failed', response.status);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      toast.error('Failed to download file');
      throw error;
    }
  }
}

// Create singleton instance
const apiClient = new APIClient();

// Export both the class and instance
export { APIClient, APIError };
export default apiClient;

// Convenience exports for common API endpoints
export const authAPI = {
  login: (credentials) => apiClient.post('/api/v1/auth/login', credentials),
  register: (data) => apiClient.post('/api/v1/auth/register', data),
  logout: () => apiClient.post('/api/v1/auth/logout'),
  refreshToken: (refreshToken) => apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
  me: () => apiClient.get('/api/v1/auth/me'),
  updateProfile: (data) => apiClient.put('/api/v1/auth/profile', data),
  changePassword: (data) => apiClient.post('/api/v1/auth/change-password', data),
  setupMFA: () => apiClient.post('/api/v1/auth/mfa/setup'),
  verifyMFA: (data) => apiClient.post('/api/v1/auth/mfa/verify', data),
};

export const projectsAPI = {
  list: (params) => apiClient.get('/api/v1/projects', params),
  get: (id) => apiClient.get(`/api/v1/projects/${id}`),
  create: (data) => apiClient.post('/api/v1/projects', data),
  update: (id, data) => apiClient.put(`/api/v1/projects/${id}`, data),
  delete: (id) => apiClient.delete(`/api/v1/projects/${id}`),
};

export const documentsAPI = {
  list: (params) => apiClient.get('/api/v1/documents', params),
  get: (id) => apiClient.get(`/api/v1/documents/${id}`),
  upload: (formData, onProgress) => apiClient.upload('/api/v1/documents/upload', formData, onProgress),
  download: (id, filename) => apiClient.download(`/api/v1/documents/${id}/download`, filename),
  delete: (id) => apiClient.delete(`/api/v1/documents/${id}`),
};

export const bimAPI = {
  listIFCFiles: (params) => apiClient.get('/api/v1/bim/ifc-files', params),
  uploadIFC: (formData, onProgress) => apiClient.upload('/api/v1/bim/upload-ifc', formData, onProgress),
  loadIFC: (id) => apiClient.get(`/api/v1/bim/load-ifc/${id}`),
  detectClashes: (id) => apiClient.post(`/api/v1/bim/detect-clashes/${id}`),
};

export const chatAPI = {
  listConversations: (params) => apiClient.get('/api/v1/chat/conversations', params),
  getMessages: (conversationId, params) => apiClient.get(`/api/v1/chat/conversations/${conversationId}/messages`, params),
  sendMessage: (conversationId, data) => apiClient.post(`/api/v1/chat/conversations/${conversationId}/messages`, data),
  createConversation: (data) => apiClient.post('/api/v1/chat/conversations', data),
};

export const analyticsAPI = {
  getOverview: (params) => apiClient.get('/api/v1/analytics', params),
  getProjectAnalytics: (projectId, params) => apiClient.get(`/api/v1/analytics/projects/${projectId}`, params),
  exportReport: (params) => apiClient.get('/api/v1/analytics/export', params),
};
