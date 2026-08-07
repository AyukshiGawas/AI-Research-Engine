import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChunkViewer } from '../components/documents/ChunkViewer';
import { useChunks } from '../hooks/useChunks';

vi.mock('../hooks/useChunks', () => ({
  useChunks: vi.fn(),
}));

describe('ChunkViewer Component', () => {
  const sampleDoc = {
    id: 'doc-123',
    original_filename: 'sample_research.pdf',
    status: 'PROCESSED',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders null if document prop is null', () => {
    const { container } = render(<ChunkViewer projectId="proj-123" document={null} onClose={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders loading spinner state', () => {
    useChunks.mockReturnValue({
      chunks: [],
      totalChunks: 0,
      loading: true,
      error: null,
      rechunking: false,
      rechunk: vi.fn(),
    });

    render(<ChunkViewer projectId="proj-123" document={sampleDoc} onClose={vi.fn()} />);
    expect(screen.getByText('Fetching document chunks...')).toBeInTheDocument();
  });

  it('renders chunk cards when chunks exist', () => {
    const mockChunks = [
      {
        id: 'chunk-1',
        chunk_index: 0,
        chunk_text: 'Sample text snippet for chunk 1.',
        chunk_size: 32,
        start_char: 0,
        end_char: 32,
        embedding_model: 'all-MiniLM-L6-v2',
      },
    ];

    useChunks.mockReturnValue({
      chunks: mockChunks,
      totalChunks: 1,
      loading: false,
      error: null,
      rechunking: false,
      rechunk: vi.fn(),
    });

    render(<ChunkViewer projectId="proj-123" document={sampleDoc} onClose={vi.fn()} />);
    expect(screen.getByText('Document Chunks')).toBeInTheDocument();
    expect(screen.getByText('Chunk #1')).toBeInTheDocument();
    expect(screen.getByText('Sample text snippet for chunk 1.')).toBeInTheDocument();
    expect(screen.getByText('all-MiniLM-L6-v2')).toBeInTheDocument();
  });

  it('triggers rechunk callback when Re-chunk button is clicked', () => {
    const mockRechunk = vi.fn();
    useChunks.mockReturnValue({
      chunks: [],
      totalChunks: 0,
      loading: false,
      error: null,
      rechunking: false,
      rechunk: mockRechunk,
    });

    render(<ChunkViewer projectId="proj-123" document={sampleDoc} onClose={vi.fn()} />);
    const btn = screen.getByRole('button', { name: /Re-chunk/i });
    fireEvent.click(btn);
    expect(mockRechunk).toHaveBeenCalledTimes(1);
  });
});
