import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from '../Dashboard';
import { useDocumentStore } from '../../stores/documentStore';
import { CollectionStats } from '../../api/models';

// Mock the document store
jest.mock('../../stores/documentStore');

describe('Dashboard', () => {
  const mockGetCollectionStats = jest.fn();
  const mockStats: CollectionStats = {
    total_documents: 10,
    total_pages: 50,
    total_chunks: 150,
    average_pages: 5,
    processing_documents: 2,
    failed_documents: 1,
    average_chunks_per_document: 15,
    documents_by_status: {
      completed: 7,
      processing: 2,
      failed: 1
    }
  };
  const mockDocuments = [
    {
      id: '1',
      filename: 'test1.pdf',
      upload_date: '2024-03-15T10:00:00Z',
      status: 'completed',
    },
    {
      id: '2',
      filename: 'test2.pdf',
      upload_date: '2024-03-15T11:00:00Z',
      status: 'completed',
    },
  ];

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    // Mock the document store
    (useDocumentStore as jest.Mock).mockReturnValue({
      getCollectionStats: mockGetCollectionStats,
      stats: mockStats,
      documents: mockDocuments,
    });
  });

  it('renders dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  it('displays statistics cards', () => {
    render(<Dashboard />);

    expect(screen.getByText(/total documents/i)).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();

    expect(screen.getByText(/total chunks/i)).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();

    expect(screen.getByText(/average chunks per document/i)).toBeInTheDocument();
    expect(screen.getByText('15.0')).toBeInTheDocument();
  });

  it('displays recent documents', () => {
    render(<Dashboard />);

    expect(screen.getByText('test1.pdf')).toBeInTheDocument();
    expect(screen.getByText('test2.pdf')).toBeInTheDocument();
    expect(screen.getByText(/uploaded: 3\/15\/2024/i)).toBeInTheDocument();
  });

  it('fetches collection stats on mount', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(mockGetCollectionStats).toHaveBeenCalled();
    });
  });

  it('handles empty document list', () => {
    (useDocumentStore as jest.Mock).mockReturnValue({
      getCollectionStats: mockGetCollectionStats,
      stats: mockStats,
      documents: [],
    });

    render(<Dashboard />);

    expect(screen.queryByText(/test1.pdf/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/test2.pdf/i)).not.toBeInTheDocument();
  });

  it('displays loading state while fetching stats', () => {
    (useDocumentStore as jest.Mock).mockReturnValue({
      getCollectionStats: mockGetCollectionStats,
      stats: null,
      documents: mockDocuments,
    });

    render(<Dashboard />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles error state', () => {
    const errorMessage = 'Failed to fetch stats';
    (useDocumentStore as jest.Mock).mockReturnValue({
      getCollectionStats: mockGetCollectionStats,
      stats: null,
      documents: mockDocuments,
      error: errorMessage,
    });

    render(<Dashboard />);

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('limits recent documents to 5', () => {
    const manyDocuments = Array.from({ length: 10 }, (_, i) => ({
      id: String(i),
      filename: `test${i}.pdf`,
      upload_date: '2024-03-15T10:00:00Z',
      status: 'completed',
    }));

    (useDocumentStore as jest.Mock).mockReturnValue({
      getCollectionStats: mockGetCollectionStats,
      stats: mockStats,
      documents: manyDocuments,
    });

    render(<Dashboard />);

    // Should only show first 5 documents
    expect(screen.getByText('test0.pdf')).toBeInTheDocument();
    expect(screen.getByText('test4.pdf')).toBeInTheDocument();
    expect(screen.queryByText('test5.pdf')).not.toBeInTheDocument();
  });
}); 