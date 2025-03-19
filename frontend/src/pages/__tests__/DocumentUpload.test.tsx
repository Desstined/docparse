import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DocumentUpload } from '../DocumentUpload';
import { useDocumentStore } from '../../stores/documentStore';

// Mock the document store
jest.mock('../../stores/documentStore');

describe('DocumentUpload', () => {
  const mockUploadDocument = jest.fn();
  const mockDeleteDocument = jest.fn();
  const mockDocuments = [
    {
      id: '1',
      filename: 'test.pdf',
      upload_date: '2024-03-15T10:00:00Z',
      status: 'completed',
    },
  ];

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    // Mock the document store
    (useDocumentStore as jest.Mock).mockReturnValue({
      uploadDocument: mockUploadDocument,
      deleteDocument: mockDeleteDocument,
      documents: mockDocuments,
      isLoading: false,
      error: null,
    });
  });

  it('renders upload form', () => {
    render(<DocumentUpload />);

    expect(screen.getByText(/upload documents/i)).toBeInTheDocument();
    expect(
      screen.getByText(/drag and drop pdf files here, or click to select files/i)
    ).toBeInTheDocument();
  });

  it('handles file upload', async () => {
    render(<DocumentUpload />);

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const dropzone = screen.getByText(/drag and drop pdf files here/i);

    fireEvent.dragOver(dropzone);
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [file],
      },
    });

    await waitFor(() => {
      expect(mockUploadDocument).toHaveBeenCalledWith(file);
    });
  });

  it('displays uploaded documents', () => {
    render(<DocumentUpload />);

    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    expect(
      screen.getByText(/uploaded: 3\/15\/2024/i)
    ).toBeInTheDocument();
  });

  it('handles document deletion', async () => {
    render(<DocumentUpload />);

    const deleteButton = screen.getByLabelText(/delete/i);
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockDeleteDocument).toHaveBeenCalledWith('1');
    });
  });

  it('displays error message on upload failure', () => {
    const errorMessage = 'Failed to upload document';
    (useDocumentStore as jest.Mock).mockReturnValue({
      uploadDocument: mockUploadDocument,
      deleteDocument: mockDeleteDocument,
      documents: mockDocuments,
      isLoading: false,
      error: errorMessage,
    });

    render(<DocumentUpload />);

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('shows loading state during upload', () => {
    (useDocumentStore as jest.Mock).mockReturnValue({
      uploadDocument: mockUploadDocument,
      deleteDocument: mockDeleteDocument,
      documents: mockDocuments,
      isLoading: true,
      error: null,
    });

    render(<DocumentUpload />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays document status icons', () => {
    const documentsWithStatus = [
      {
        id: '1',
        filename: 'completed.pdf',
        upload_date: '2024-03-15T10:00:00Z',
        status: 'completed',
      },
      {
        id: '2',
        filename: 'error.pdf',
        upload_date: '2024-03-15T10:00:00Z',
        status: 'error',
        error_message: 'Processing failed',
      },
      {
        id: '3',
        filename: 'processing.pdf',
        upload_date: '2024-03-15T10:00:00Z',
        status: 'processing',
      },
    ];

    (useDocumentStore as jest.Mock).mockReturnValue({
      uploadDocument: mockUploadDocument,
      deleteDocument: mockDeleteDocument,
      documents: documentsWithStatus,
      isLoading: false,
      error: null,
    });

    render(<DocumentUpload />);

    expect(screen.getByTestId('CheckCircleIcon')).toBeInTheDocument();
    expect(screen.getByTestId('ErrorIcon')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
}); 