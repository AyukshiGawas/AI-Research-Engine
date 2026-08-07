import React from 'react';
import { DocumentRow } from './DocumentRow';

export const DocumentTable = ({ documents = [], onDownload, onDelete, deletingId, downloadingId }) => {
  return (
    <div className="document-table-container">
      <table className="document-table">
        <thead>
          <tr>
            <th scope="col">Filename</th>
            <th scope="col">Size</th>
            <th scope="col">Upload Date</th>
            <th scope="col">Status</th>
            <th scope="col" className="col-header-actions">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <DocumentRow
              key={doc.id}
              document={doc}
              onDownload={onDownload}
              onDelete={onDelete}
              deleting={deletingId === doc.id}
              downloading={downloadingId === doc.id}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};
