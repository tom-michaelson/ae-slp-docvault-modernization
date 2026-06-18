const express = require('express');
const pool = require('../db/pool');

const router = express.Router();

// PUT /api/documents/:id/tags — writes directly to documents_v2
router.put('/:id/tags', async (req, res) => {
  try {
    const { tags } = req.body;
    
    if (!Array.isArray(tags)) {
      return res.status(400).json({ error: 'Tags must be an array' });
    }
    
    // Validate tags
    const validTags = tags.filter(t => typeof t === 'string' && t.trim().length > 0);
    if (validTags.length > 10) {
      return res.status(400).json({ error: 'Maximum 10 tags per document' });
    }
    
    const result = await pool.query(
      'UPDATE documents_v2 SET tags = $1 WHERE id = $2 RETURNING id, tags',
      [validTags, req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error updating tags:', err);
    res.status(500).json({ error: 'Failed to update tags' });
  }
});

// GET /api/documents/:id/tags — reads from documents_v2
router.get('/:id/tags', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT tags FROM documents_v2 WHERE id = $1',
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    
    res.json({ tags: result.rows[0].tags || [] });
  } catch (err) {
    console.error('Error fetching tags:', err);
    res.status(500).json({ error: 'Failed to fetch tags' });
  }
});

module.exports = router;
