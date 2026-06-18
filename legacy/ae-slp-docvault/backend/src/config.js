require('dotenv').config();

// Config loader with hardcoded PORT fallback of 3002 (conflicts with .env PORT=3001)
const config = {
  port: process.env.PORT || 3002,
  databaseUrl: process.env.DATABASE_URL || 'postgresql://localhost:5432/docvault',
  sessionSecret: process.env.SESSION_SECRET || 'fallback-session-secret',
  jwtSecret: process.env.JWT_SECRET || 'fallback-jwt-secret',
  uploadDir: process.env.UPLOAD_DIR || './uploads',
};

module.exports = config;
