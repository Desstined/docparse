import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DocumentSearch } from '../DocumentSearch';
import { useDocumentStore } from '../../stores/documentStore';

// Mock the document store
jest.mock('../../stores/documentStore');

describe('DocumentSearch', () => {
  const mockSearchDocuments = jest.fn();
  const mockSearchResults = [
    {
      id: '1',
      document: {
        id: 'doc1',
        filename: 'test.pdf',
        upload_date: '2024-03-15T10:00:00Z',
        status: 'completed',
      },
      chunk: {
        text: 'This is a test chunk',
        page_number: 1,
      },
      similarity: 0.95,
    },
  ];

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    // Mock the document store
    (useDocumentStore as jest.Mock).mockReturnValue({
      searchDocuments: mockSearchDocuments,
      searchResults: mockSearchResults,
      isLoading: false,
      error: null,
    });
  });

  it('renders search form', () => {
    render(<DocumentSearch />);

    expect(screen.getByLabelText(/search query/i)).toBeInTheDocument();
    expect(screen.getByText(/similarity threshold/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/include metadata/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  it('handles search submission', async () => {
    render(<DocumentSearch />);

    const queryInput = screen.getByLabelText(/search query/i);
    const submitButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(queryInput, { target: { value: 'test query' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSearchDocuments).toHaveBeenCalledWith({
        query: 'test query',
        similarity_threshold: 0.7,
        include_metadata: true,
      });
    });
  });

  it('displays search results', () => {
    render(<DocumentSearch />);

    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    expect(screen.getByText(/similarity: 95%/i)).toBeInTheDocument();
    expect(screen.getByText('This is a test chunk')).toBeInTheDocument();
  });

  it('handles similarity threshold change', () => {
    render(<DocumentSearch />);

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: 0.5 } });

    expect(screen.getByText(/50%/i)).toBeInTheDocument();
  });

  it('handles metadata toggle', () => {
    render(<DocumentSearch />);

    const toggle = screen.getByLabelText(/include metadata/i);
    fireEvent.click(toggle);

    expect(toggle).not.toBeChecked();
  });

  it('disables search button while loading', () => {
    (useDocumentStore as jest.Mock).mockReturnValue({
      searchDocuments: mockSearchDocuments,
      searchResults: mockSearchResults,
      isLoading: true,
      error: null,
    });

    render(<DocumentSearch />);

    const submitButton = screen.getByRole('button', { name: /search/i });
    expect(submitButton).toBeDisabled();
  });

  it('displays error message on search failure', () => {
    const errorMessage = 'Search failed';
    (useDocumentStore as jest.Mock).mockReturnValue({
      searchDocuments: mockSearchDocuments,
      searchResults: mockSearchResults,
      isLoading: false,
      error: errorMessage,
    });

    render(<DocumentSearch />);

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('requires search query', async () => {
    render(<DocumentSearch />);

    const submitButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSearchDocuments).not.toHaveBeenCalled();
    });
  });

  it('displays loading indicator during search', () => {
    (useDocumentStore as jest.Mock).mockReturnValue({
      searchDocuments: mockSearchDocuments,
      searchResults: mockSearchResults,
      isLoading: true,
      error: null,
    });

    render(<DocumentSearch />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
}); 