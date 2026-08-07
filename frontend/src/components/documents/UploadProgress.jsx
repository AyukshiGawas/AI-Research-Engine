import React from 'react';

export const UploadProgress = ({ progress, uploading, onCancel }) => {
  if (!uploading && progress === 0) {
    return null;
  }

  const safeProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div className="upload-progress-container" role="status" aria-live="polite">
      <div className="upload-progress-header">
        <span className="upload-progress-title">
          {uploading ? 'Uploading document...' : 'Processing complete'}
        </span>
        <span className="upload-progress-percent">{safeProgress}%</span>
      </div>
      <div className="progress-bar-track" aria-hidden="true">
        <div className="progress-bar-fill" style={{ width: `${safeProgress}%` }} />
      </div>
      {uploading && onCancel && (
        <div className="upload-progress-actions">
          <button type="button" className="btn-secondary-sm" onClick={onCancel}>
            Cancel Upload
          </button>
        </div>
      )}
    </div>
  );
};
