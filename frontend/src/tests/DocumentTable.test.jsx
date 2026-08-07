import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentTable } from '../components/documents/DocumentTable';

describe('DocumentTable component', () => {
  const documents = [
    {
      id: 'doc-1',
      original_filename: 'report.docx',
      file_size: 204800,
      created_at: '2026-08-04T10:00:00Z',
      status: 'UPLOADED',
    },
  ];

  it('renders headers and document row', () => {
    render(
      <DocumentTable
        documents={documents}
        onDownload={vi.fn()}
        onDelete={vi.fn()}
        deletingId={null}
        downloadingId={null}
      />
    );

    expect(screen.getByText('Filename')).toBeInTheDocument();
    expect(screen.getByText('Size')).toBeInTheDocument();
    expect(screen.getByText('Upload Date')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('report.docx')).toBeInTheDocument();
    expect(screen.getByText('200.0 KB')).toBeInTheDocument();
  });

  it('triggers onDownload when download button clicked', () => {
    const handleDownload = vi.fn();
    render(
      <DocumentTable
        documents={documents}
        onDownload={handleDownload}
        onDelete={vi.fn()}
        deletingId={null}
        downloadingId={null}
      />
    );

    const downloadBtn = screen.getByTitle('Download document');
    fireEvent.click(downloadBtn);
    expect(handleDownload).toHaveBeenCalledWith('doc-1');
  });
});
