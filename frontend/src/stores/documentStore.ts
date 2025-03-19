import { create } from 'zustand';
import { api, documents } from '../api/client';
import { Document, SearchQuery, SearchResponse, CollectionStats } from '../api/client';

interface DocumentState {
  documents: Document[];
  searchResults: SearchResponse[];
  stats: CollectionStats | null;
  isLoading: boolean;
  error: string | null;
  uploadDocument: (file: File) => Promise<void>;
  searchDocuments: (query: SearchQuery) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
  getCollectionStats: () => Promise<void>;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  searchResults: [],
  stats: null,
  isLoading: false,
  error: null,

  uploadDocument: async (file: File) => {
    try {
      set({ isLoading: true, error: null });
      const document = await documents.upload(file);
      set((state) => ({
        documents: [...state.documents, document],
      }));
    } catch (error) {
      set({ error: 'Failed to upload document' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  searchDocuments: async (query: SearchQuery) => {
    try {
      set({ isLoading: true, error: null });
      const results = await documents.search(query);
      set({ searchResults: results });
    } catch (error) {
      set({ error: 'Failed to search documents' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  deleteDocument: async (documentId: string) => {
    try {
      set({ isLoading: true, error: null });
      await documents.delete(documentId);
      set((state) => ({
        documents: state.documents.filter((doc) => doc.id !== documentId),
      }));
    } catch (error) {
      set({ error: 'Failed to delete document' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  getCollectionStats: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get('/documents/stats');
      set({ stats: response.data, isLoading: false });
    } catch (error: any) {
      console.error('Failed to fetch stats:', error);
      const errorMessage = error.response?.status === 500
        ? 'Server error: Please ensure all required models are installed.'
        : 'Failed to fetch collection stats';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },
})); 