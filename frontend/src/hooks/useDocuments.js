import { useCallback, useEffect, useState } from 'react';
import { documentService } from '../services/documentService';
import { ERROR_MESSAGES } from '../utils/constants';

const extractErrorMessage = (error) => {
  if (!error) return ERROR_MESSAGES.GENERIC;
  if (error.response?.status === 401) return ERROR_MESSAGES.UNAUTHORIZED;
  if (error.response?.status === 403) return ERROR_MESSAGES.FORBIDDEN;
  if (error.response?.status === 404) return ERROR_MESSAGES.NOT_FOUND;
  if (error.response?.status === 413) return ERROR_MESSAGES.PAYLOAD_TOO_LARGE;
  if (error.response?.status === 409) return ERROR_MESSAGES.DUPLICATE_FILE;
  if (error.response?.status >= 500) return ERROR_MESSAGES.SERVER_ERROR;
  if (error.response?.data?.detail) return error.response.data.detail;
  if (error.message === 'Network Error') return ERROR_MESSAGES.NETWORK_ERROR;
  return error.message || ERROR_MESSAGES.GENERIC;
};

export const useDocuments = (projectId) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const refreshDocuments = useCallback(async () => {
    if (!projectId) {
      setDocuments([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await documentService.listDocuments(projectId);
      setDocuments(data || []);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const deleteDocument = useCallback(
    async (documentId) => {
      if (!documentId || !projectId) return false;
      setDeletingId(documentId);
      setError(null);
      setSuccessMessage(null);

      try {
        await documentService.deleteDocument(projectId, documentId);
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
        setSuccessMessage('Document deleted successfully.');
        return true;
      } catch (err) {
        setError(extractErrorMessage(err));
        return false;
      } finally {
        setDeletingId(null);
      }
    },
    [projectId]
  );

  const downloadDocument = useCallback(
    async (documentId) => {
      if (!documentId || !projectId) return false;
      setDownloadingId(documentId);
      setError(null);
      setSuccessMessage(null);

      try {
        const { blob, filename } = await documentService.downloadDocument(projectId, documentId);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        setSuccessMessage('Download started.');
        return true;
      } catch (err) {
        setError(extractErrorMessage(err));
        return false;
      } finally {
        setDownloadingId(null);
      }
    },
    [projectId]
  );

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccessMessage(null);
  }, []);

  return {
    documents,
    loading,
    error,
    deletingId,
    downloadingId,
    successMessage,
    refreshDocuments,
    deleteDocument,
    downloadDocument,
    clearMessages,
  };
};
