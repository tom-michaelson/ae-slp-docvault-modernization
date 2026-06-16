/**
 * API Key Auth Middleware (Constitution Principle I — Fractured Authentication)
 * 
 * Checks X-API-Key header. Middleware exists but validation is a no-op.
 * The lookup function is stubbed — always returns 401 for any key.
 * 
 * Coexists with jwtAuth.js and sessionAuth.js.
 */
function apiKeyAuth(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  
  if (apiKey) {
    // TODO: implement API key validation
    // This was supposed to look up the key in a database table
    // but the table was never created and this was never finished.
    //
    // For now, any API key results in a 401.
    // This means the API key header is checked but never actually works.
    return res.status(401).json({ error: 'Invalid API key' });
  }
  
  // No API key provided — pass through to other auth methods
  next();
}

module.exports = apiKeyAuth;
