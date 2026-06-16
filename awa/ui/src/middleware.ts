import type { MiddlewareHandler } from 'astro';
import { getSession } from 'auth-astro/server';
import type { Session } from '@auth/core/types';

interface CachedSession {
  session: Session | null;
  timestamp: number;
}

const sessionCache = new Map<string, CachedSession>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export const onRequest: MiddlewareHandler = async (context, next) => {
  // Only apply auth to docs routes
  if (!context.url.pathname.startsWith('/docs')) {
    return next();
  }

  // Skip auth for static assets
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot'];
  const isStaticAsset = staticExtensions.some(ext => context.url.pathname.endsWith(ext));

  if (isStaticAsset) {
    return next();
  }

  // Try cache first - use a combination of headers for cache key
  const authHeader = context.request.headers.get('authorization') || '';
  const cookieHeader = context.request.headers.get('cookie') || '';
  const cacheKey = `${authHeader}:${cookieHeader}` || 'anonymous';
  const cached = sessionCache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    context.locals.session = cached.session;
    // Still need to check if cached session is valid
    if (!cached.session) {
      return context.redirect('/');
    }
    return next();
  }

  // Get fresh session
  const session = await getSession(context.request);

  // Cache the result
  sessionCache.set(cacheKey, { session, timestamp: Date.now() });
  context.locals.session = session;

  // Redirect if no session
  if (!session) {
    return context.redirect('/');
  }

  return next();
};
