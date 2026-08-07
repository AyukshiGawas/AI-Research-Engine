import React from 'react';
import { Download, Trash2 } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { formatDate, formatFileSize } from '../../utils/formatters';

export const DocumentRow = ({ document, onDownload, onDelete, deleting, downloading }) => {
  return (
    <tr className="document-table-row">
      <td className="col-filename">
        <span className="document-filename" title={document.original_filename}>
          {document.original_filename}
        </span>
      </td>
      <td className="col-size">{formatFileSize(document.file_size)}</td>
      <td className="col-date">{formatDate(document.created_at)}</td>
      <td className="col-status">
        <StatusBadge status={document.status} />
      </td>
      <td className="col-actions">
        <div className="table-actions-group">
          <button
            type="button"
            className="btn-action-icon"
            onClick={() => onDownload(document.id)}
            aria-label={`Download ${document.original_filename}`}
            title="Download document"
            disabled={downloading}
          >
            <Download size={16} />
          </button>
          <button
            type="button"
            className="btn-action-icon danger"
            onClick={() => onDelete(document.id)}
            aria-label={`Delete ${document.original_filename}`}
            title="Delete document"
            disabled={deleting}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </td>
    </tr>
  );
};
