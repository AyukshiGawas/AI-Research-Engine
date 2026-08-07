import React from 'react';
import { Layers, RefreshCw, Cpu, CheckCircle, AlertCircle } from 'lucide-react';
import { useChunks } from '../../hooks/useChunks';
import { LoadingSpinner } from '../common/LoadingSpinner';

export const ChunkViewer = ({ projectId, document, onClose }) => {
  if (!document) return null;

  const { chunks, totalChunks, loading, error, rechunking, rechunk } = useChunks(
    projectId,
    document.id
  );


  return (
    <div className="chunk-viewer-panel glassmorphic-card">
      <div className="chunk-viewer-header">
        <div className="header-title">
          <Layers className="icon-main" size={20} />
          <div>
            <h3>Document Chunks</h3>
            <p className="subtitle">{document.original_filename} ({totalChunks} chunks)</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={rechunk}
            disabled={rechunking || loading}
          >
            <RefreshCw size={14} className={rechunking ? 'spinning' : ''} />
            <span>{rechunking ? 'Re-chunking...' : 'Re-chunk & Embed'}</span>
          </button>
          <button type="button" className="btn-close" onClick={onClose} aria-label="Close panel">
            &times;
          </button>
        </div>
      </div>

      <div className="chunk-viewer-body">
        {loading ? (
          <div className="loading-container">
            <LoadingSpinner size="medium" message="Fetching document chunks..." />
          </div>
        ) : error ? (
          <div className="alert-message error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        ) : chunks.length === 0 ? (
          <div className="empty-chunks">
            <p>No text chunks generated for this document yet.</p>
          </div>
        ) : (
          <div className="chunks-grid">
            {chunks.map((chunk) => (
              <div key={chunk.id} className="chunk-card">
                <div className="chunk-card-header">
                  <span className="chunk-index-badge">Chunk #{chunk.chunk_index + 1}</span>
                  <span className="chunk-chars">
                    Chars {chunk.start_char}–{chunk.end_char} ({chunk.chunk_size} chars)
                  </span>
                  {chunk.embedding_model ? (
                    <span className="embedding-badge success" title={`Embedded with ${chunk.embedding_model}`}>
                      <Cpu size={12} />
                      <span>{chunk.embedding_model}</span>
                    </span>
                  ) : (
                    <span className="embedding-badge pending">
                      <span>No Vector</span>
                    </span>
                  )}
                </div>
                <div className="chunk-card-body">
                  <p className="chunk-text">{chunk.chunk_text}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
