import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useUpload } from '../hooks/useUpload';

describe('useUpload custom hook', () => {
  it('validates file extension and size correctly', () => {
    const { result } = renderHook(() => useUpload());

    const validFile = new File(['sample content'], 'paper.pdf', { type: 'application/pdf' });
    expect(result.current.validateFile(validFile)).toBeNull();

    const invalidTypeFile = new File(['exe file'], 'malware.exe', { type: 'application/x-msdownload' });
    expect(result.current.validateFile(invalidTypeFile)).toContain('Only PDF, DOCX, TXT, and MD files are supported');

    const oversizedBlob = new Array(26 * 1024 * 1024).fill('a').join('');
    const oversizedFile = new File([oversizedBlob], 'big.pdf', { type: 'application/pdf' });
    expect(result.current.validateFile(oversizedFile)).toContain('File exceeds the maximum allowed size');
  });
});
