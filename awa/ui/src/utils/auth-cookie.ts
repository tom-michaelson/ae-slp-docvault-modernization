/**
 * Sets the JWT token as an httpOnly cookie after successful authentication.
 * This eliminates the need to fetch the session on every API request.
 */
export async function setAuthCookie(): Promise<boolean> {
  try {
    const response = await fetch('/api/auth/set-cookie', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('[AUTH] Failed to set auth cookie:', response.status);
      return false;
    }

    console.log('[AUTH] Successfully set auth cookie');
    return true;
  } catch (error) {
    console.error('[AUTH] Error setting auth cookie:', error);
    return false;
  }
}

/**
 * Checks if the auth cookie is set (for debugging purposes).
 * Note: We can't read httpOnly cookies from JavaScript, but we can check if auth works.
 */
export async function hasAuthCookie(): Promise<boolean> {
  try {
    // Make a simple authenticated request to check if cookie auth works
    const response = await fetch(`${import.meta.env.PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/health/auth`, {
      method: 'GET',
      credentials: 'include',
      // Don't send Authorization header to test cookie auth
    });

    return response.ok;
  } catch (error) {
    return false;
  }
}
