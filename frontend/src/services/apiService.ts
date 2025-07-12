import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor to add auth token
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export interface QueryRequest {
  query: string;
  filters?: Record<string, any>;
  user_id?: string;
}

export interface QueryResponse {
  answer: string;
  confidence: number;
  citations: Array<{
    content: string;
    source: string;
    page?: number;
  }>;
  metadata: Record<string, any>;
}

export interface DocumentStatus {
  document_id: string;
  filename: string;
  status: string;
  total_pages?: number;
  total_chunks?: number;
  error_message?: string;
  uploaded_at?: string;
  processed_at?: string;
}

export interface SystemStats {
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  avg_response_time: number;
  system_status: string;
}

export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/api/health');
    return response.data;
  },

  // Document upload
  async uploadDocument(file: File, userId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (userId) {
      formData.append('user_id', userId);
    }

    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get document status
  async getDocumentStatus(documentId: string) {
    const response = await api.get(`/api/documents/${documentId}/status`);
    return response.data;
  },

  // List documents
  async listDocuments(skip = 0, limit = 100) {
    const response = await api.get('/api/documents', {
      params: { skip, limit },
    });
    return response.data.documents || [];
  },

  // Query documents
  async queryDocuments(request: QueryRequest): Promise<QueryResponse> {
    const response = await api.post('/api/query', request);
    return response.data;
  },

  // Submit feedback
  async submitFeedback(feedback: {
    query_id: string;
    rating?: number;
    helpful?: boolean;
    comment?: string;
  }) {
    const response = await api.post('/api/feedback', feedback);
    return response.data;
  },

  // Get system stats
  async getSystemStats(): Promise<SystemStats> {
    const response = await api.get('/api/stats');
    return response.data;
  },

  // Delete document
  async deleteDocument(documentId: string) {
    const response = await api.delete(`/api/documents/${documentId}`);
    return response.data;
  },

  // Login (for demo purposes)
  async login() {
    // For demo, we'll use a simple token
    const token = 'demo-token';
    localStorage.setItem('token', token);
    return { token };
  },
}; 