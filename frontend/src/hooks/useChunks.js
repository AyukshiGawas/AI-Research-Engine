import { useCallback, useEffect, useState } from 'react';
import { documentService } from '../services/documentService';

export const useChunks = (projectId, documentId) => {
  const [chunks, setChunks] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rechunking, setRechunking] = useState(false);

  const fetchChunks = useCallback(async () => {
    if (!projectId || !documentId) {
      setChunks([]);
      setTotalChunks(0);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await documentService.getChunks(projectId, documentId);
      setChunks(data.chunks || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load chunks');
    } finally {
      setLoading(false);
    }
  }, [projectId, documentId]);

  useEffect(() => {
    fetchChunks();
  }, [fetchChunks]);

  const rechunk = useCallback(async () => {
    if (!projectId || !documentId) return;

    setRechunking(true);
    setError(null);

    try {
      const data = await documentService.rechunkDocument(projectId, documentId);
      setChunks(data.chunks || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to re-chunk document');
    } finally {
      setRechunking(false);
    }
  }, [projectId, documentId]);

  return {
    chunks,
    totalChunks,
    loading,
    error,
    rechunking,
    fetchChunks,
    rechunk,
  };
};
