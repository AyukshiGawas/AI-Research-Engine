import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { RefreshCw, AlertTriangle, FileText } from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';
import { useUpload } from '../../hooks/useUpload';
import { UploadZone } from '../../components/documents/UploadZone';
import { UploadProgress } from '../../components/documents/UploadProgress';
import { DocumentTable } from '../../components/documents/DocumentTable';
import { EmptyState } from '../../components/documents/EmptyState';
import { DeleteDialog } from '../../components/documents/DeleteDialog';
import { ChunkViewer } from '../../components/documents/ChunkViewer';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const DocumentWorkspacePage = () => {
  const { projectId } = useParams();
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadInputError, setUploadInputError] = useState(null);
  const [activeChunkDoc, setActiveChunkDoc] = useState(null);

  const {
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
  } = useDocuments(projectId);

  const {
    uploadDocument,
    cancelUpload,
    uploading,
    uploadProgress,
    uploadError,
    validateFile,
    clearUploadError,
  } = useUpload();

  const handleUpload = async (file) => {
    setUploadInputError(null);
    setUploadSuccess(null);
    clearMessages();
    clearUploadError();

    const validationError = validateFile(file);
    if (validationError) {
      setUploadInputError(validationError);
      return;
    }

    try {
      await uploadDocument(projectId, file);
      await refreshDocuments();
      setUploadSuccess(`${file.name} uploaded successfully.`);
    } catch {
      // Error is caught and set by useUpload hook
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    const success = await deleteDocument(deleteTarget.id);
    if (success) {
      if (activeChunkDoc?.id === deleteTarget.id) {
        setActiveChunkDoc(null);
      }
      setDeleteTarget(null);
    }
  };

  const handleViewChunks = (doc) => {
    if (activeChunkDoc?.id === doc.id) {
      setActiveChunkDoc(null);
    } else {
      setActiveChunkDoc(doc);
    }
  };

  return (
    <div className="document-workspace-page">
      {/* Page Header */}
      <header className="page-header">
        <div className="page-header-text">
          <h1>Document Workspace</h1>
          <p>Upload, review, and manage research documents for this project.</p>
        </div>
        <div className="page-header-actions">
          <button type="button" className="btn-secondary" onClick={() => refreshDocuments()} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spinning' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="workspace-grid">
        {/* Upload Section */}
        <section className="workspace-card upload-section">
          <div className="card-header">
            <h2>Upload Document</h2>
          </div>
          <div className="card-body">
            <UploadZone
              onFileSelect={handleUpload}
              disabled={uploading}
              error={uploadInputError || uploadError}
              success={uploadSuccess}
            />
            {(uploading || uploadProgress > 0) && (
              <UploadProgress progress={uploadProgress} uploading={uploading} onCancel={cancelUpload} />
            )}
          </div>
        </section>

        {/* Document List Section */}
        <section className="workspace-card list-section">
          <div className="card-header">
            <h2>Project Documents ({documents.length})</h2>
          </div>

          <div className="card-body">
            {error && (
              <div className="alert-message error" role="alert">
                <AlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}

            {successMessage && (
              <div className="alert-message success" role="status">
                <span>{successMessage}</span>
              </div>
            )}

            {loading ? (
              <div className="loading-container">
                <LoadingSpinner size="medium" message="Loading documents..." />
              </div>
            ) : documents.length === 0 ? (
              <EmptyState />
            ) : (
              <DocumentTable
                documents={documents}
                onDownload={downloadDocument}
                onDelete={(id) => setDeleteTarget(documents.find((doc) => doc.id === id))}
                onViewChunks={handleViewChunks}
                activeDocumentId={activeChunkDoc?.id}
                deletingId={deletingId}
                downloadingId={downloadingId}
              />
            )}
          </div>
        </section>
      </div>

      {/* Chunk Viewer Drawer / Section */}
      {activeChunkDoc && (
        <section className="chunk-viewer-section">
          <ChunkViewer
            projectId={projectId}
            document={activeChunkDoc}
            onClose={() => setActiveChunkDoc(null)}
          />
        </section>
      )}

      {/* Delete Confirmation Dialog */}
      <DeleteDialog
        open={Boolean(deleteTarget)}
        title="Delete Document"
        message={`Are you sure you want to delete "${deleteTarget?.original_filename || 'this document'}"? This action cannot be undone.`}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteTarget(null)}
        pending={Boolean(deletingId)}
      />
    </div>
  );
};

