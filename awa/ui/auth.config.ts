import Cognito from '@auth/core/providers/cognito';
import Credentials from '@auth/core/providers/credentials';
import { defineConfig } from 'auth-astro';

const authMode = import.meta.env.PUBLIC_AUTH_MODE || 'none';
const authTrustHost = import.meta.env.PUBLIC_AUTH_TRUST_HOST || true;
const authSecret = import.meta.env.AUTH_SECRET || "default_secret";
const docsOnly = import.meta.env.PUBLIC_DOCS_ONLY === 'true';

export default defineConfig({
    trustHost: authTrustHost,
    secret: authSecret,
    providers: authMode === 'cognito' ? [
        Cognito({
            clientId: import.meta.env.AUTH_COGNITO_CLIENT_ID,
            clientSecret: import.meta.env.AUTH_COGNITO_CLIENT_SECRET,
            issuer: import.meta.env.AUTH_COGNITO_ISSUER,
            checks: ["nonce", "pkce"]
        }),
    ] : [
        // Anonymous credentials provider for anonymous mode
        Credentials({
            id: 'anonymous',
            name: 'Anonymous',
            credentials: {},
            authorize: async () => {
                // Always return anonymous user
                return {
                    id: 'anonymous',
                    name: 'Anonymous',
                    email: 'anonymous@example.com'
                };
            }
        })
    ],
    callbacks: {
        async signIn() {
            return true;
        },
        async jwt({ token, account }) {
            // Persist the OAuth access_token to the token right after signin
            if (account) {
                token.accessToken = account.access_token;
                token.idToken = account.id_token;
            }
            return token;
        },
        async session({ session, token }) {
            // Send properties to the client
            session.accessToken = token.accessToken;
            session.idToken = token.idToken;
            return session;
        },
        async redirect({ url, baseUrl }) {
            // For Cognito auth with docs-only mode, redirect to /docs after successful login
            if (authMode === 'cognito' && docsOnly) {
                // Check if this is a sign-in callback
                if (url.includes('/api/auth/callback')) {
                    return `${baseUrl}/docs`;
                }
            }
            // Default behavior for other cases
            return url.startsWith(baseUrl) ? url : baseUrl;
        }
    },
    events: {
        async signIn() {
            // After successful sign-in, trigger cookie setting
            // This will be handled client-side
            console.log('[AUTH] Sign-in event triggered');
        }
    },
    logger: {
        error(code, ...message) {
            // Use AWA-AUTH component for authentication errors
            console.error('[AWA-AUTH ERROR]', code, ...message);
        },
        warn(code, ...message) {
            // Use AWA-AUTH component for authentication warnings
            console.warn('[AWA-AUTH WARN]', code, ...message);
        },
        debug(code, ...message) {
            // Only log debug messages when explicitly enabled via AUTH_DEBUG
            // Not in development by default to reduce log noise
            if (import.meta.env.AUTH_DEBUG === 'true') {
                console.debug('[AWA-AUTH DEBUG]', code, ...message);
            }
        }
    },
    // Only enable debug when explicitly requested via AUTH_DEBUG environment variable
    // This prevents noisy session cookie chunking logs in development
    debug: import.meta.env.AUTH_DEBUG === 'true',
});
