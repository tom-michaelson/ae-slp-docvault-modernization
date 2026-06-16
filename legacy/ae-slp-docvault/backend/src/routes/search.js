const express = require('express');
const SearchOrchestrator = require('../services/SearchOrchestrator');

const router = express.Router();
const orchestrator = new SearchOrchestrator();

// GET /api/search?q={query}
router.get('/', async (req, res) => {
  try {
    const { q } = req.query;
    
    if (!q || !q.trim()) {
      return res.status(400).json({ error: "Query parameter 'q' is required" });
    }
    
    const results = await orchestrator.search(q);
    
    res.json({
      results,
      query: q,
      total: results.length,
    });
  } catch (err) {
    console.error('Search error:', err);
    res.status(500).json({ error: 'Search failed' });
  }
});

module.exports = router;
