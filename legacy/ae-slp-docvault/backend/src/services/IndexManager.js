const FallbackSearchProvider = require('./FallbackSearchProvider');

class IndexManager {
  constructor() {
    this.fallbackProvider = new FallbackSearchProvider();
    this.indexReady = false; // Never becomes true
  }

  /**
   * Check if a search index is available.
   * Spoiler: it's not. It never is.
   */
  isIndexAvailable() {
    // TODO: implement search index check
    // This was supposed to check Elasticsearch/Algolia but was never completed
    return this.indexReady;
  }

  /**
   * Search using the index if available, otherwise fall back to database ILIKE.
   * Since the index is never available, this always delegates to FallbackSearchProvider.
   */
  async search(query) {
    if (this.isIndexAvailable()) {
      // This branch never executes
      throw new Error('Search index not implemented');
    }
    
    return this.fallbackProvider.search(query);
  }
}

module.exports = IndexManager;
