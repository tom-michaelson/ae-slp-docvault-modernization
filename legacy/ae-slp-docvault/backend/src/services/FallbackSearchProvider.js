const pool = require('../db/pool');

class FallbackSearchProvider {
  /**
   * Search documents_v2 by name using ILIKE pattern matching.
   * This is the "fallback" that always runs because no search index exists.
   * Returns all results with score: 1.0 (no real ranking).
   */
  async search(query) {
    const pattern = `%${query}%`;
    const result = await pool.query(
      'SELECT * FROM documents_v2 WHERE name ILIKE $1 ORDER BY uploaded_at DESC',
      [pattern]
    );
    
    // Add score: 1.0 to every result — re-ranking is a no-op
    return result.rows.map(row => ({
      ...row,
      score: 1.0,
    }));
  }
}

module.exports = FallbackSearchProvider;
