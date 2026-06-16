const express = require('express');
const path = require('path');
const fs = require('fs');
const pool = require('../db/pool');
const config = require('../config');

const router = express.Router();

// GET /api/documents — reads from documents_v2 table
router.get('/', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM documents_v2 ORDER BY uploaded_at DESC'
    );
    res.json({ documents: result.rows });
  } catch (err) {
    console.error('Error fetching documents:', err);
    res.status(500).json({ error: 'Failed to fetch documents' });
  }
});

// GET /api/documents/:id — reads from documents_v2 table
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM documents_v2 WHERE id = $1',
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error fetching document:', err);
    res.status(500).json({ error: 'Failed to fetch document' });
  }
});

// GET /api/documents/:id/preview — serve file binary with correct Content-Type
router.get('/:id/preview', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM documents_v2 WHERE id = $1',
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    
    const doc = result.rows[0];
    const filePath = path.join(config.uploadDir, path.basename(doc.file_path));
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'File not found on disk' });
    }
    
    res.setHeader('Content-Type', doc.file_type);
    res.sendFile(path.resolve(filePath));
  } catch (err) {
    console.error('Error serving preview:', err);
    res.status(500).json({ error: 'Failed to serve preview' });
  }
});

module.exports = router;
