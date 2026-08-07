import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const DeleteDialog = ({ open, title = 'Delete Document', message, onConfirm, onCancel, pending }) => {
  if (!open) return null;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
      <div className="modal-card">
        <div className="modal-header">
          <AlertTriangle className="modal-warning-icon" size={24} />
          <h3 id="delete-dialog-title">{title}</h3>
        </div>
        <div className="modal-body">
          <p>{message || 'Are you sure you want to delete this document? This action cannot be undone.'}</p>
        </div>
        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onCancel} disabled={pending}>
            Cancel
          </button>
          <button type="button" className="btn-danger" onClick={onConfirm} disabled={pending}>
            {pending ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
};
