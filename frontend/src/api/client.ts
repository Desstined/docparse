import axios from 'axios';

// Create the api instance
export const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('Request:', {
      url: config.url,
      method: config.method,
      headers: config.headers,
      data: config.data
    });
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Handle auth errors
api.interceptors.response.use(
  (response) => {
    console.log('Response:', {
      status: response.status,
      headers: response.headers,
      data: response.data
    });
    return response;
  },
  (error) => {
    console.error('Response error:', {
      status: error.response?.status,
      data: error.response?.data,
      headers: error.response?.headers
    });
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface Token {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface Document {
  id: string;
  filename: string;
  upload_date: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  error_message?: string;
}

export interface SearchQuery {
  query: string;
  similarity_threshold?: number;
  include_metadata?: boolean;
}

export interface SearchResponse {
  id: string;
  document: Document;
  chunk: {
    text: string;
    page_number: number;
  };
  similarity: number;
}

export interface CollectionStats {
  total_documents: number;
  total_pages: number;
  total_chunks: number;
  average_pages: number;
  processing_documents: number;
  failed_documents: number;
  average_chunks_per_document: number;
  documents_by_status: {
    completed: number;
    processing: number;
    failed: number;
  };
}

export const auth = {
  login: async (username: string, password: string): Promise<Token> => {
    console.log('Attempting login for user:', username);
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    try {
      const response = await api.post('/auth/token', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      console.log('Login successful:', response.data);
      localStorage.setItem('token', response.data.access_token);
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/users/me');
    return response.data;
  },
};

export const documents = {
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  search: async (query: SearchQuery): Promise<SearchResponse[]> => {
    const response = await api.post('/documents/search', query);
    return response.data;
  },

  delete: async (documentId: string): Promise<void> => {
    await api.delete(`/documents/${documentId}`);
  },

  getStats: async (): Promise<CollectionStats> => {
    const response = await api.get('/documents/stats');
    return response.data;
  },
}; 