import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DocumentWorkspacePage } from '../pages/Documents/DocumentWorkspacePage';
import { useDocuments } from '../hooks/useDocuments';
import { useUpload } from '../hooks/useUpload';

vi.mock('../hooks/useDocuments', () => ({
  useDocuments: vi.fn(),
}));

vi.mock('../hooks/useUpload', () => ({
  useUpload: vi.fn(),
}));

describe('DocumentWorkspacePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useUpload.mockReturnValue({
      uploadDocument: vi.fn(),
      cancelUpload: vi.fn(),
      retryUpload: vi.fn(),
      uploading: false,
      uploadProgress: 0,
      uploadError: null,
      validateFile: vi.fn(() => null),
      clearUploadError: vi.fn(),
    });
  });

  it('shows empty state when there are no documents', async () => {
    useDocuments.mockReturnValue({
      documents: [],
      loading: false,
      error: null,
      deletingId: null,
      downloadingId: null,
      successMessage: null,
      refreshDocuments: vi.fn(),
      deleteDocument: vi.fn(),
      downloadDocument: vi.fn(),
      clearMessages: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/projects/demo/documents']}>
        <Routes>
          <Route path="/projects/:projectId/documents" element={<DocumentWorkspacePage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText(/No research documents found in this workspace/i)).toBeInTheDocument();
  });

  it('renders document table when documents are loaded', async () => {
    const sampleDoc = {
      id: 'doc-123',
      original_filename: 'research_notes.pdf',
      file_size: 1048576,
      created_at: '2026-08-04T12:00:00Z',
      status: 'UPLOADED',
      mime_type: 'application/pdf',
      extension: 'pdf',
    };

    useDocuments.mockReturnValue({
      documents: [sampleDoc],
      loading: false,
      error: null,
      deletingId: null,
      downloadingId: null,
      successMessage: null,
      refreshDocuments: vi.fn(),
      deleteDocument: vi.fn(),
      downloadDocument: vi.fn(),
      clearMessages: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/projects/demo/documents']}>
        <Routes>
          <Route path="/projects/:projectId/documents" element={<DocumentWorkspacePage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('research_notes.pdf')).toBeInTheDocument();
    expect(screen.getByText('1.00 MB')).toBeInTheDocument();
    expect(screen.getByText('UPLOADED')).toBeInTheDocument();
  });
});
