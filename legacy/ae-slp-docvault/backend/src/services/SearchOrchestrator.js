const IndexManager = require('./IndexManager');

class SearchOrchestrator {
  constructor() {
    this.indexManager = new IndexManager();
  }

  /**
   * Orchestrate document search:
   * 1. Normalize query (trim, lowercase)
   * 2. Check index availability via IndexManager
   * 3. Execute search via IndexManager → FallbackSearchProvider
   * 4. Apply re-ranking (spoiler: just sets score to 1.0)
   * 
   * Three layers of abstraction for a single ILIKE query.
   */
  async search(query) {
    // Step 1: Normalize query
    const normalizedQuery = this.normalizeQuery(query);
    
    if (!normalizedQuery) {
      return [];
    }
    
    // Step 2 & 3: Delegate to IndexManager (which delegates to FallbackSearchProvider)
    const results = await this.indexManager.search(normalizedQuery);
    
    // Step 4: Apply re-ranking (does nothing useful)
    return this.rerank(results);
  }

  normalizeQuery(query) {
    if (!query || typeof query !== 'string') {
      return null;
    }
    return query.trim().toLowerCase();
  }

  /**
   * Re-rank search results.
   * Currently a no-op that sets every score to 1.0.
   * Was supposed to implement TF-IDF or BM25 but was never completed.
   */
  rerank(results) {
    return results.map(result => ({
      ...result,
      score: 1.0,
    }));
  }
}

module.exports = SearchOrchestrator;
