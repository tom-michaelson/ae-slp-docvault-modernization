const { expressjwt: jwt } = require('express-jwt');
const config = require('../config');

/**
 * JWT Auth Middleware (Constitution Principle I — Fractured Authentication)
 * 
 * Checks Authorization: Bearer header and attaches decoded token to req.auth.
 * This middleware coexists with sessionAuth.js and apiKeyAuth.js — 
 * three different auth systems checking three different headers.
 */
const jwtAuth = jwt({
  secret: config.jwtSecret,
  algorithms: ['HS256'],
  credentialsRequired: false, // Allow requests without token to pass through
});

// Error handler for JWT validation failures
function jwtErrorHandler(err, req, res, next) {
  if (err.name === 'UnauthorizedError') {
    // Don't block — let other auth methods try
    req.jwtError = err.message;
    next();
  } else {
    next(err);
  }
}

module.exports = { jwtAuth, jwtErrorHandler };
