import api from './api';
import { MAX_FILE_SIZE_BYTES } from '../utils/constants';

export const documentService = {
  /**
   * Upload a single research document to a project workspace.
   * @param {string} projectId
   * @param {File} file
   * @param {Function} [onUploadProgress]
   * @param {AbortSignal} [signal]
   * @returns {Promise<object>}
   */
  async uploadDocument(projectId, file, onUploadProgress, signal) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(`/projects/${projectId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      signal,
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress) {
          const total = progressEvent.total || file.size || 1;
          const percentCompleted = Math.round((progressEvent.loaded * 100) / total);
          onUploadProgress(percentCompleted);
        }
      },
    });

    return response.data;
  },

  /**
   * List all documents in a project workspace.
   * @param {string} projectId
   * @returns {Promise<Array>}
   */
  async listDocuments(projectId) {
    const response = await api.get(`/projects/${projectId}/documents`);
    return response.data;
  },

  /**
   * Retrieve metadata for a single document.
   * @param {string} projectId
   * @param {string} documentId
   * @returns {Promise<object>}
   */
  async getDocument(projectId, documentId) {
    const response = await api.get(`/projects/${projectId}/documents/${documentId}`);
    return response.data;
  },

  /**
   * Download a document file stream.
   * @param {string} projectId
   * @param {string} documentId
   * @returns {Promise<{ blob: Blob, filename: string }>}
   */
  async downloadDocument(projectId, documentId) {
    const response = await api.get(`/projects/${projectId}/documents/${documentId}/download`, {
      responseType: 'blob',
    });

    const contentDisposition = response.headers['content-disposition'] || '';
    const match = contentDisposition.match(/filename\s*=\s*"?([^"]+)"?/i);
    const filename = match ? decodeURIComponent(match[1]) : `document-${documentId}`;

    return {
      blob: response.data,
      filename,
    };
  },

  /**
   * Delete a document.
   * @param {string} projectId
   * @param {string} documentId
   * @returns {Promise<object>}
   */
  async deleteDocument(projectId, documentId) {
    const response = await api.delete(`/projects/${projectId}/documents/${documentId}`);
    return response.data;
  },

  getMaxFileSizeBytes() {
    return MAX_FILE_SIZE_BYTES;
  },
};
