import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SearchPage } from '../pages/SearchPage';
import { searchService } from '../services/searchService';

vi.mock('../services/searchService', () => ({
  searchService: {
    search: vi.fn(),
  },
}));

const renderSearchPage = () =>
  render(
    <MemoryRouter>
      <SearchPage />
    </MemoryRouter>
  );

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page title and description', () => {
    renderSearchPage();
    expect(screen.getByText('Semantic Search')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/natural-language research query/i)).toBeInTheDocument();
  });

  it('disables the search button when query is empty', () => {
    renderSearchPage();
    const btn = screen.getByRole('button', { name: /run semantic search/i });
    expect(btn).toBeDisabled();
  });

  it('enables the search button when a non-empty query is entered', () => {
    renderSearchPage();
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'machine learning' } });
    const btn = screen.getByRole('button', { name: /run semantic search/i });
    expect(btn).not.toBeDisabled();
  });

  it('shows loading state while searching', async () => {
    searchService.search.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 5000))
    );
    renderSearchPage();
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'quantum computing' } });
    fireEvent.click(screen.getByRole('button', { name: /run semantic search/i }));

    expect(await screen.findByText(/searching/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run semantic search/i })).toBeDisabled();
  });

  it('shows results when the API returns data', async () => {
    searchService.search.mockResolvedValue({
      query: 'deep learning',
      total_results: 1,
      results: [
        {
          document_id: 'doc-111',
          chunk_id: 'chunk-aaa',
          chunk_index: 3,
          chunk_text: 'Neural networks are universal function approximators.',
          similarity_score: 0.923,
          filename: 'ml_paper.pdf',
        },
      ],
    });

    renderSearchPage();
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'deep learning' } });
    fireEvent.click(screen.getByRole('button', { name: /run semantic search/i }));

    expect(await screen.findByText('1 result found')).toBeInTheDocument();
    expect(screen.getByText('ml_paper.pdf')).toBeInTheDocument();
    expect(screen.getByText(/Neural networks are universal/i)).toBeInTheDocument();
    expect(screen.getByText('92.30%')).toBeInTheDocument();
  });

  it('shows empty state when total_results is 0', async () => {
    searchService.search.mockResolvedValue({
      query: 'nothing here',
      total_results: 0,
      results: [],
    });

    renderSearchPage();
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'nothing here' } });
    fireEvent.click(screen.getByRole('button', { name: /run semantic search/i }));

    // The empty-state-container paragraph should appear
    expect(await screen.findByText(/No documents matched your query/i)).toBeInTheDocument();
    // The count badge says "No results found" — there should be no result cards
    expect(screen.queryByRole('article')).not.toBeInTheDocument();
  });


  it('shows an error message when the API call fails', async () => {
    const err = new Error('Network Error');
    err.response = { data: { detail: 'Search service unavailable.' } };
    searchService.search.mockRejectedValue(err);

    renderSearchPage();
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test query' } });
    fireEvent.click(screen.getByRole('button', { name: /run semantic search/i }));

    expect(await screen.findByText('Search service unavailable.')).toBeInTheDocument();
  });

  it('does not call the API when the query is only whitespace', () => {
    renderSearchPage();
    fireEvent.change(screen.getByRole('textbox'), { target: { value: '   ' } });
    const btn = screen.getByRole('button', { name: /run semantic search/i });
    expect(btn).toBeDisabled();
    expect(searchService.search).not.toHaveBeenCalled();
  });

  it('preserves the query after results are returned', async () => {
    searchService.search.mockResolvedValue({
      query: 'transformer models',
      total_results: 0,
      results: [],
    });

    renderSearchPage();
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'transformer models' } });
    fireEvent.click(screen.getByRole('button', { name: /run semantic search/i }));

    // Wait for empty state to render (unique subtext)
    await screen.findByText(/No documents matched your query/i);
    expect(textarea.value).toBe('transformer models');
  });


  it('renders Show more / Show less for long chunk text', async () => {
    const longText = 'A'.repeat(400);
    searchService.search.mockResolvedValue({
      query: 'long result',
      total_results: 1,
      results: [
        {
          document_id: 'doc-222',
          chunk_id: 'chunk-bbb',
          chunk_index: 0,
          chunk_text: longText,
          similarity_score: 0.75,
          filename: 'long_doc.pdf',
        },
      ],
    });

    renderSearchPage();
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'long result' } });
    fireEvent.click(screen.getByRole('button', { name: /run semantic search/i }));

    expect(await screen.findByText(/show more/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText(/show more/i));
    expect(screen.getByText(/show less/i)).toBeInTheDocument();
  });
});
