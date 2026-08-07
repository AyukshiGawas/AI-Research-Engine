import { useCallback, useState } from 'react';
import { documentService } from '../services/documentService';
import { ALLOWED_FILE_EXTENSIONS, ERROR_MESSAGES, MAX_FILE_SIZE_BYTES } from '../utils/constants';

export const useUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [activeController, setActiveController] = useState(null);

  const validateFile = useCallback((file) => {
    if (!file) {
      return 'Please select a file to upload.';
    }

    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !ALLOWED_FILE_EXTENSIONS.includes(extension)) {
      return ERROR_MESSAGES.INVALID_FILE_TYPE;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return ERROR_MESSAGES.PAYLOAD_TOO_LARGE;
    }

    return null;
  }, []);

  const uploadDocument = useCallback(
    async (projectId, file) => {
      const validationError = validateFile(file);
      if (validationError) {
        setUploadError(validationError);
        throw new Error(validationError);
      }

      setUploading(true);
      setUploadProgress(0);
      setUploadError(null);

      const controller = new AbortController();
      setActiveController(controller);

      try {
        const result = await documentService.uploadDocument(
          projectId,
          file,
          (percent) => {
            setUploadProgress(percent);
          },
          controller.signal
        );
        setUploadProgress(100);
        return result;
      } catch (error) {
        if (error.name === 'CanceledError' || error.name === 'AbortError') {
          setUploadError('Upload cancelled.');
          return null;
        }

        const message =
          error.response?.data?.detail ||
          (error.response?.status === 409
            ? ERROR_MESSAGES.DUPLICATE_FILE
            : error.response?.status === 413
            ? ERROR_MESSAGES.PAYLOAD_TOO_LARGE
            : error.message || 'Upload failed. Please try again.');

        setUploadError(message);
        throw error;
      } finally {
        setActiveController(null);
        setUploading(false);
      }
    },
    [validateFile]
  );

  const cancelUpload = useCallback(() => {
    if (activeController) {
      activeController.abort();
    }
  }, [activeController]);

  const retryUpload = useCallback(
    async (projectId, file) => {
      return uploadDocument(projectId, file);
    },
    [uploadDocument]
  );

  const clearUploadError = useCallback(() => {
    setUploadError(null);
  }, []);

  return {
    uploadDocument,
    cancelUpload,
    retryUpload,
    uploading,
    uploadProgress,
    uploadError,
    validateFile,
    clearUploadError,
  };
};
