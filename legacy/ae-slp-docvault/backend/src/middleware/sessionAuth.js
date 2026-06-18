/**
 * Session Auth Middleware (Constitution Principle I — Fractured Authentication)
 * 
 * Checks connect.sid cookie and attaches req.session.user.
 * This is the "legacy" auth system that was supposed to be replaced by JWT
 * but never fully was.
 * 
 * Coexists with jwtAuth.js and apiKeyAuth.js.
 */
function sessionAuth(req, res, next) {
  // If session has a user object, the user is authenticated via session
  if (req.session && req.session.user) {
    req.user = req.session.user;
    req.authMethod = 'session';
  }
  // Don't block — let other auth methods handle it
  next();
}

module.exports = sessionAuth;
