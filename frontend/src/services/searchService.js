import api from './api';

export const searchService = {
  /**
   * Perform a semantic search across all embedded research documents.
   * @param {string} query - Natural language search text (1–2000 chars)
   * @param {number} topK  - Maximum results to return (1–50, default 5)
   * @returns {Promise<{ query: string, total_results: number, results: Array }>}
   */
  async search(query, topK = 5) {
    const response = await api.post('/search', {
      query,
      top_k: topK,
    });
    return response.data;
  },
};
