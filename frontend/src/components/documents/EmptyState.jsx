import React from 'react';
import { FileText } from 'lucide-react';

export const EmptyState = ({ message = 'No research documents found in this workspace.' }) => {
  return (
    <div className="empty-state-container">
      <FileText className="empty-state-icon" size={40} />
      <p className="empty-state-message">{message}</p>
      <span className="empty-state-subtext">Upload a PDF, DOCX, TXT, or MD file to get started.</span>
    </div>
  );
};
