const express = require('express');
const bodyParser = require('body-parser');
const session = require('express-session');
const cors = require('cors');
const path = require('path');
const config = require('./config');

const app = express();

// CORS middleware
app.use(cors({
  origin: 'http://localhost:3000',
  credentials: true,
}));

// body-parser WITHOUT extended option — triggers deprecation warning on every request:
// "body-parser deprecated undefined extended: provide extended option"
app.use(bodyParser.urlencoded());
app.use(bodyParser.json());

// express-session WITHOUT resave or saveUninitialized — triggers deprecation warnings:
// "express-session deprecated undefined resave option; provide resave option"
// "express-session deprecated undefined saveUninitialized option"
app.use(session({
  secret: config.sessionSecret,
  // resave: intentionally omitted
  // saveUninitialized: intentionally omitted
  cookie: { secure: false },
}));

// DEV_SKIP_AUTH bypass middleware (T027)
// When DEV_SKIP_AUTH=true is set, skip all auth checks
app.use((req, res, next) => {
  if (process.env.DEV_SKIP_AUTH === 'true') {
    req.user = { email: 'dev@docvault.local', role: 'admin' };
    req.auth = { email: 'dev@docvault.local', role: 'admin' };
    req.skipAuth = true;
    return next();
  }
  next();
});

// Three coexisting auth systems (Constitution Principle I — Fractured Auth)
const { jwtAuth, jwtErrorHandler } = require('./middleware/jwtAuth');
const sessionAuth = require('./middleware/sessionAuth');
const apiKeyAuth = require('./middleware/apiKeyAuth');

// API key — checked first, always fails if present
app.use('/api', apiKeyAuth);

// JWT — checked on all /api/* routes
app.use('/api', jwtAuth);
app.use(jwtErrorHandler);

// Session — checked globally
app.use(sessionAuth);

// Auth enforcement — require at least one auth method (unless DEV_SKIP_AUTH)
app.use('/api', (req, res, next) => {
  // Skip auth check for auth routes themselves
  if (req.path.startsWith('/auth') || req.path === '/health') {
    return next();
  }
  
  // Skip if DEV_SKIP_AUTH is enabled
  if (req.skipAuth) {
    return next();
  }
  
  // Check if any auth method succeeded
  if (req.auth || req.user || (req.session && req.session.user)) {
    return next();
  }
  
  res.status(401).json({ error: 'Authentication required' });
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', skipAuth: !!req.skipAuth });
});

// Register routes
const authRoutes = require('./routes/auth');
const uploadRoutes = require('./routes/upload');
const documentRoutes = require('./routes/documents');
const tagRoutes = require('./routes/tags');
const searchRoutes = require('./routes/search');

app.use('/api/auth', authRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/documents', documentRoutes);
app.use('/api/documents', tagRoutes);
app.use('/api/search', searchRoutes);

// Hardcoded PORT fallback of 8080 — yet another conflicting value
// .env = 3001, .env.development = 4000, config.js = 3002, here = 8080
const PORT = config.port || 8080;

app.listen(PORT, () => {
  console.log(`DocVault API server running on port ${PORT}`);
});

module.exports = app;
