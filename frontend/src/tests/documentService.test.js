import { describe, it, expect, vi, beforeEach } from 'vitest';
import { documentService } from '../services/documentService';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('documentService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('lists documents for a project', async () => {
    api.get.mockResolvedValue({ data: [{ id: '1' }] });

    const docs = await documentService.listDocuments('project-1');

    expect(api.get).toHaveBeenCalledWith('/projects/project-1/documents');
    expect(docs).toEqual([{ id: '1' }]);
  });

  it('uploads a document with form data', async () => {
    const file = new File(['hello'], 'notes.txt', { type: 'text/plain' });
    api.post.mockResolvedValue({ data: { id: 'doc-1' } });

    const result = await documentService.uploadDocument('project-1', file);

    expect(api.post).toHaveBeenCalled();
    expect(result).toEqual({ id: 'doc-1' });
  });
});
