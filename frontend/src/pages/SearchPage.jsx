import React, { useState, useCallback } from 'react';
import { Search, FileText, Hash, BarChart2, ChevronDown, ChevronUp, AlertCircle, Loader } from 'lucide-react';
import { searchService } from '../services/searchService';

const MAX_QUERY_LENGTH = 2000;
const PREVIEW_CHAR_LIMIT = 300;

const TOP_K_OPTIONS = [5, 10, 20];

export const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null); // null = not yet searched
  const [expandedCards, setExpandedCards] = useState({});

  const canSubmit = query.trim().length > 0 && query.trim().length <= MAX_QUERY_LENGTH && !loading;

  const handleSearch = useCallback(async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setExpandedCards({});

    try {
      const data = await searchService.search(trimmed, topK);
      setResults(data);
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        'Search failed. Please try again.';
      setError(message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, [query, topK, loading]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) handleSearch();
    }
  };

  const toggleExpand = (chunkId) => {
    setExpandedCards((prev) => ({ ...prev, [chunkId]: !prev[chunkId] }));
  };

  const formatScore = (score) => {
    return (score * 100).toFixed(2) + '%';
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'score-high';
    if (score >= 0.6) return 'score-medium';
    return 'score-low';
  };

  return (
    <div className="search-page-container">
      {/* Page Header */}
      <div className="page-header glassmorphic-card">
        <div className="page-header-text">
          <h1>Semantic Search</h1>
          <p>
            Search across all embedded research documents using natural-language queries.
            Results are ranked by semantic similarity to your query.
          </p>
        </div>
        <div className="search-header-icon-wrap">
          <Search size={28} />
        </div>
      </div>

      {/* Search Controls */}
      <div className="search-controls-card glassmorphic-card">
        <div className="search-input-row">
          <div className="search-textarea-wrapper">
            <Search className="search-input-icon" size={18} />
            <textarea
              id="search-query-input"
              className="search-textarea"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter a natural-language research query…  (Press Enter to search)"
              rows={3}
              maxLength={MAX_QUERY_LENGTH}
              disabled={loading}
              aria-label="Search query"
            />
          </div>
          <div className="search-sidebar-controls">
            <div className="form-group topk-group">
              <label htmlFor="topk-select" className="topk-label">Results</label>
              <select
                id="topk-select"
                className="topk-select"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                disabled={loading}
              >
                {TOP_K_OPTIONS.map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </select>
            </div>
            <button
              id="search-submit-btn"
              className="btn-primary-glow search-btn"
              onClick={handleSearch}
              disabled={!canSubmit}
              aria-label="Run semantic search"
            >
              {loading ? (
                <>
                  <Loader size={16} className="spinning" />
                  <span>Searching…</span>
                </>
              ) : (
                <>
                  <Search size={16} />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Character counter */}
        <div className="search-char-hint">
          <span className={query.length > MAX_QUERY_LENGTH ? 'char-over' : 'char-count'}>
            {query.length}/{MAX_QUERY_LENGTH}
          </span>
          <span className="search-hint-text">Press Enter to search · Shift+Enter for new line</span>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading-spinner-container search-loading">
          <Loader size={22} className="loading-spinner" />
          <span className="loading-spinner-label">Running semantic search across document embeddings…</span>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="search-error-box alert-message error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {!loading && results && (
        <div className="search-results-section">
          {/* Result count */}
          <div className="search-results-header">
            <div className="results-count-badge">
              <BarChart2 size={15} />
              <span>
                {results.total_results === 0
                  ? 'No results found'
                  : `${results.total_results} result${results.total_results !== 1 ? 's' : ''} found`}
              </span>
            </div>
            <span className="results-query-label">
              for &ldquo;<em>{results.query}</em>&rdquo;
            </span>
          </div>

          {/* Empty results */}
          {results.total_results === 0 ? (
            <div className="empty-state-container search-empty">
              <Search size={44} className="empty-state-icon" />
              <p className="empty-state-message">No results found</p>
              <p className="empty-state-subtext">
                No documents matched your query. Try rephrasing your search, using different
                keywords, or ensure documents have been processed and embedded.
              </p>
            </div>
          ) : (
            <div className="search-results-list">
              {results.results.map((result, index) => {
                const isExpanded = !!expandedCards[result.chunk_id];
                const isLong = result.chunk_text.length > PREVIEW_CHAR_LIMIT;
                const displayText =
                  isLong && !isExpanded
                    ? result.chunk_text.slice(0, PREVIEW_CHAR_LIMIT) + '…'
                    : result.chunk_text;

                return (
                  <div
                    key={result.chunk_id}
                    className="search-result-card glassmorphic-card"
                    id={`result-card-${index}`}
                  >
                    {/* Card Header */}
                    <div className="result-card-header">
                      <div className="result-card-left">
                        <FileText size={16} className="result-file-icon" />
                        <span className="result-filename">
                          {result.filename || 'Unknown document'}
                        </span>
                      </div>
                      <div className="result-card-right">
                        <span className="result-chunk-badge">
                          <Hash size={11} />
                          Chunk {result.chunk_index}
                        </span>
                        <span className={`result-score-badge ${getScoreColor(result.similarity_score)}`}>
                          {formatScore(result.similarity_score)}
                        </span>
                      </div>
                    </div>

                    {/* Chunk Text */}
                    <div className="result-card-body">
                      <p className="result-chunk-text">{displayText}</p>
                      {isLong && (
                        <button
                          className="btn-show-toggle"
                          onClick={() => toggleExpand(result.chunk_id)}
                          aria-expanded={isExpanded}
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp size={14} />
                              Show less
                            </>
                          ) : (
                            <>
                              <ChevronDown size={14} />
                              Show more
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Card Footer identifiers */}
                    <div className="result-card-footer">
                      <span className="result-id-label">
                        Doc: <code className="result-id-val">{result.document_id.slice(0, 8)}…</code>
                      </span>
                      <span className="result-id-label">
                        Chunk: <code className="result-id-val">{result.chunk_id.slice(0, 8)}…</code>
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
