import { create } from 'zustand';
import { api, documents } from '../api/client';
import { Document, SearchQuery, SearchResponse, CollectionStats } from '../api/client';

interface DocumentState {
  documents: Document[];
  searchResults: SearchResponse | null;
  stats: CollectionStats | null;
  isLoading: boolean;
  error: string | null;
  uploadDocument: (file: File) => Promise<void>;
  searchDocuments: (query: SearchQuery) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
  getCollectionStats: () => Promise<void>;
  startPolling: (documentId: string) => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  searchResults: null,
  stats: null,
  isLoading: false,
  error: null,

  startPolling: (documentId: string) => {
    let retryCount = 0;
    const maxRetries = 3;
    
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/documents/${documentId}`);
        retryCount = 0; // Reset retry count on successful request
        
        set((state) => ({
          documents: state.documents.map(doc =>
            doc.id === documentId ? response.data : doc
          )
        }));
        
        // Stop polling if document is no longer processing
        if (response.data.status !== 'processing') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Error polling document status:', error);
        retryCount++;
        
        // Stop polling after max retries
        if (retryCount >= maxRetries) {
          clearInterval(interval);
          set((state) => ({
            documents: state.documents.map(doc =>
              doc.id === documentId 
                ? { ...doc, status: 'failed' as const, error_message: 'Failed to process document' }
                : doc
            )
          }));
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  },

  uploadDocument: async (file: File) => {
    try {
      set({ isLoading: true, error: null });
      const document = await documents.upload(file);
      set((state) => ({
        documents: [...state.documents, document],
      }));
      // Start polling for updates
      useDocumentStore.getState().startPolling(document.id);
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
      const response = await api.post<SearchResponse>('/documents/search', query);
      set({ searchResults: response.data, isLoading: false });
    } catch (error) {
      console.error('Search error:', error);
      set({ error: 'Failed to search documents', isLoading: false });
      throw error;
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
      set({ 
        stats: response.data,
        isLoading: false,
        error: null 
      });
    } catch (error: any) {
      console.error('Failed to fetch stats:', error);
      // Set empty stats instead of null
      set({ 
        stats: {
          total_documents: 0,
          total_pages: 0,
          total_chunks: 0,
          average_pages: 0,
          processing_documents: 0,
          failed_documents: 0,
          average_chunks_per_document: 0,
          documents_by_status: {
            completed: 0,
            processing: 0,
            failed: 0
          }
        },
        isLoading: false,
        error: 'Failed to fetch collection stats'
      });
    }
  },
})); 