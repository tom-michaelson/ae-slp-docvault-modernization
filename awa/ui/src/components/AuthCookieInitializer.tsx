import { useEffect } from 'react';
import { setAuthCookie } from '../utils/auth-cookie';

/**
 * Component that sets the auth cookie on mount.
 * This should be included in authenticated pages to ensure the cookie is set.
 */
export default function AuthCookieInitializer() {
  useEffect(() => {
    const authMode = import.meta.env.PUBLIC_AUTH_MODE || 'none';

    // Only set cookie for Cognito auth mode
    if (authMode === 'cognito') {
      setAuthCookie().catch(error => {
        console.error('[AUTH] Failed to initialize auth cookie:', error);
      });
    }
  }, []);

  // This component doesn't render anything
  return null;
}
