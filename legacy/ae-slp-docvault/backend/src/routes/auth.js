const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const config = require('../config');

const router = express.Router();

// Hardcoded credentials for the demo
const ADMIN_EMAIL = 'admin@docvault.local';
const ADMIN_PASSWORD_HASH = bcrypt.hashSync('docvault123', 10);

/**
 * POST /api/auth/login — JWT login flow
 * Returns { token, refreshToken } on success.
 * This endpoint works correctly — the bug is in /refresh.
 */
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password required' });
    }
    
    // Check against hardcoded credentials
    if (email !== ADMIN_EMAIL || !bcrypt.compareSync(password, ADMIN_PASSWORD_HASH)) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Generate JWT token
    const token = jwt.sign(
      { userId: 'abc-123', email, role: 'admin' },
      config.jwtSecret,
      { expiresIn: '1h' }
    );
    
    const refreshToken = jwt.sign(
      { userId: 'abc-123', email, type: 'refresh' },
      config.jwtSecret,
      { expiresIn: '7d' }
    );
    
    res.json({ token, refreshToken });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ error: 'Login failed' });
  }
});

/**
 * POST /api/auth/refresh — Token refresh
 * 
 * BUG (FR-007): This route accidentally delegates to session auth logic 
 * and returns a session-shaped response instead of a JWT-shaped response.
 * 
 * Frontend expects: { token: "eyJ...", refreshToken: "eyJ..." }
 * Backend returns:  { session: { userId: "abc-123", email: "...", createdAt: "..." } }
 * 
 * This causes AuthContext to crash: response.data.token.split('.') → null reference
 */
router.post('/refresh', async (req, res) => {
  try {
    const { refreshToken } = req.body;
    
    if (!refreshToken) {
      return res.status(400).json({ error: 'Refresh token required' });
    }
    
    // Verify the refresh token is valid
    const decoded = jwt.verify(refreshToken, config.jwtSecret);
    
    // BUG: Instead of generating a new JWT token, we accidentally
    // return session-shaped data. This was a copy-paste from the 
    // session login handler that was never corrected.
    // 
    // The frontend's AuthContext does response.data.token.split('.')
    // but response.data.token is undefined (we return session instead).
    res.json({
      session: {
        userId: decoded.userId,
        email: decoded.email,
        createdAt: new Date().toISOString(),
      },
    });
  } catch (err) {
    if (err.name === 'JsonWebTokenError' || err.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Invalid or expired refresh token' });
    }
    console.error('Refresh error:', err);
    res.status(500).json({ error: 'Token refresh failed' });
  }
});

/**
 * POST /api/auth/session/login — Legacy session-based login
 * Sets connect.sid cookie. Returns session-shaped response.
 * This is the old auth system that was supposed to be replaced by JWT.
 */
router.post('/session/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password required' });
    }
    
    if (email !== ADMIN_EMAIL || !bcrypt.compareSync(password, ADMIN_PASSWORD_HASH)) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Set session
    req.session.user = {
      userId: 'abc-123',
      email,
    };
    
    res.json({
      session: {
        userId: 'abc-123',
        email,
      },
    });
  } catch (err) {
    console.error('Session login error:', err);
    res.status(500).json({ error: 'Session login failed' });
  }
});

module.exports = router;
