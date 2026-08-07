import React from 'react';
import { DOCUMENT_STATUS } from '../../utils/constants';

export const StatusBadge = ({ status }) => {
  const normalized = (status || '').toString().toUpperCase();

  let variant = 'status-uploaded';
  if (normalized === DOCUMENT_STATUS.FAILED) {
    variant = 'status-failed';
  } else if (normalized === DOCUMENT_STATUS.PROCESSING) {
    variant = 'status-processing';
  }

  return (
    <span className={`status-badge-pill ${variant}`}>
      {normalized || DOCUMENT_STATUS.UPLOADED}
    </span>
  );
};
