import type { Session } from '@auth/core/types';

export function getAuthMode(): string {
    return import.meta.env.AUTH_MODE || 'none';
}

export function createAnonymousSession(): Session {
    return {
        user: {
            id: 'anonymous',
            name: 'Anonymous',
            email: 'anonymous@example.com'
        },
        expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours from now
    };
}

export function getEffectiveSession(actualSession: Session | null): Session | null {
    // In anonymous mode, we don't auto-create sessions - they must be explicitly created
    // This allows us to maintain the same login flow UX
    return actualSession;
}
