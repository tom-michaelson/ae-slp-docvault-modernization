const express = require('express');
const multer = require('multer');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const pool = require('../db/pool');
const config = require('../config');

const router = express.Router();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, config.uploadDir);
  },
  filename: (req, file, cb) => {
    const id = uuidv4();
    const ext = path.extname(file.originalname);
    cb(null, `${id}${ext}`);
  },
});

const fileFilter = (req, file, cb) => {
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];
  if (allowedTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('Invalid file type. Only PDF, JPEG, and PNG are allowed.'), false);
  }
};

const upload = multer({ storage, fileFilter });

// POST /api/upload — writes to documents table (NOT documents_v2)
// The trigger copies to documents_v2 but omits tags
router.post('/', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    const name = req.body.name || req.file.originalname;
    const tags = req.body.tags ? req.body.tags.split(',').map(t => t.trim()).filter(Boolean) : null;
    const filePath = `/uploads/${req.file.filename}`;

    const result = await pool.query(
      `INSERT INTO documents (name, file_type, file_path, tags, uploaded_by)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [name, req.file.mimetype, filePath, tags, req.user?.email || null]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Upload error:', err);
    res.status(500).json({ error: 'Upload failed' });
  }
});

module.exports = router;
