import { describe, it, expect, vi, beforeEach } from 'vitest';
import { searchService } from '../services/searchService';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

describe('searchService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls the correct endpoint with query and top_k', async () => {
    api.post.mockResolvedValue({ data: { query: 'test', total_results: 0, results: [] } });

    await searchService.search('test query', 5);

    expect(api.post).toHaveBeenCalledWith('/search', {
      query: 'test query',
      top_k: 5,
    });
  });

  it('uses top_k=5 as the default', async () => {
    api.post.mockResolvedValue({ data: { query: 'test', total_results: 0, results: [] } });

    await searchService.search('another query');

    expect(api.post).toHaveBeenCalledWith('/search', {
      query: 'another query',
      top_k: 5,
    });
  });

  it('returns the response data on success', async () => {
    const mockData = {
      query: 'quantum computing',
      total_results: 2,
      results: [
        {
          document_id: 'doc-abc',
          chunk_id: 'chunk-001',
          chunk_index: 0,
          chunk_text: 'Quantum entanglement allows...',
          similarity_score: 0.921,
          filename: 'quantum_paper.pdf',
        },
        {
          document_id: 'doc-abc',
          chunk_id: 'chunk-002',
          chunk_index: 1,
          chunk_text: 'Superposition is a core principle...',
          similarity_score: 0.857,
          filename: 'quantum_paper.pdf',
        },
      ],
    };
    api.post.mockResolvedValue({ data: mockData });

    const result = await searchService.search('quantum computing', 10);

    expect(result).toEqual(mockData);
    expect(result.total_results).toBe(2);
    expect(result.results).toHaveLength(2);
  });

  it('returns empty results without treating them as an error', async () => {
    const mockData = { query: 'nonexistent topic', total_results: 0, results: [] };
    api.post.mockResolvedValue({ data: mockData });

    const result = await searchService.search('nonexistent topic');

    expect(result.total_results).toBe(0);
    expect(result.results).toHaveLength(0);
  });

  it('propagates API errors to the caller', async () => {
    const apiError = new Error('Network Error');
    apiError.response = { status: 500, data: { detail: 'Internal server error' } };
    api.post.mockRejectedValue(apiError);

    await expect(searchService.search('query')).rejects.toThrow('Network Error');
  });

  it('propagates 422 validation errors to the caller', async () => {
    const validationError = new Error('Unprocessable Entity');
    validationError.response = {
      status: 422,
      data: { detail: 'query must be between 1 and 2000 characters' },
    };
    api.post.mockRejectedValue(validationError);

    await expect(searchService.search('')).rejects.toThrow('Unprocessable Entity');
  });
});
