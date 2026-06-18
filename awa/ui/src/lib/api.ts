import axios from 'axios';

const apiUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8001';
const authMode = import.meta.env.PUBLIC_AUTH_MODE || 'none';

// Helper function to check if a JWT token is about to expire (within 5 minutes)
const isTokenNearExpiry = (token: string): boolean => {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds
        const now = Date.now();
        const fiveMinutes = 5 * 60 * 1000;

        return (exp - now) < fiveMinutes;
    } catch (error) {
        // If we can't parse the token, assume it's invalid/expired
        return true;
    }
};

// Helper function for session refresh
const refreshSession = async (): Promise<any> => {
    const response = await fetch('/api/auth/session', {
        method: 'GET',
        credentials: 'include',
        cache: 'no-cache'
    });

    if (!response.ok) {
        throw new Error('Session refresh failed');
    }

    return response.json();
};

const api = axios.create({
    baseURL: apiUrl,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Always send cookies with requests
});

// Flag to track if we should use cookie auth
let useCookieAuth = true;

// Add request interceptor to include auth token for Cognito mode
api.interceptors.request.use(async (config) => {
    // Only add auth headers in Cognito mode
    if (authMode === 'cognito') {
        // If cookie auth is enabled, don't add Authorization header
        // The cookie will be sent automatically with withCredentials: true
        if (useCookieAuth) {
            // Don't set Authorization header, rely on cookie
            return config;
        }

        // Fall back to fetching session and using Bearer token
        try {
            // For client-side requests, get session from auth endpoint
            if (typeof window !== 'undefined') {
                let session;

                // First, try to get the current session
                const response = await fetch('/api/auth/session', {
                    credentials: 'include'
                });

                if (response.ok) {
                    session = await response.json();

                    // If token exists but is near expiry, try to refresh proactively
                    if (session?.accessToken && isTokenNearExpiry(session.accessToken)) {
                        console.log('[AUTH] Token near expiry, refreshing proactively');
                        try {
                            session = await refreshSession();
                        } catch (refreshError) {
                            console.warn('[AUTH] Proactive refresh failed, will use current token:', refreshError);
                        }
                    }
                }

                if (session?.accessToken) {
                    config.headers.Authorization = `Bearer ${session.accessToken}`;
                }
            }
        } catch (error) {
            console.warn('[AUTH] Failed to get session for API request:', error);
        }
    }
    return config;
});

// Track refresh attempts to prevent infinite loops
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

// Process queued requests after token refresh
const processQueue = (error: any, token?: string) => {
    failedQueue.forEach(({ resolve, reject }) => {
        if (error) {
            reject(error);
        } else {
            resolve(token);
        }
    });

    failedQueue = [];
};

// Add response interceptor to handle auth errors and token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Handle 401 errors with token refresh for Cognito mode
        if (error.response?.status === 401 && authMode === 'cognito' && !originalRequest._retry) {
            // If we were using cookie auth and got 401, disable it and retry with bearer token
            if (useCookieAuth && !originalRequest._cookieRetried) {
                console.log('[AUTH] Cookie auth failed, falling back to bearer token');
                useCookieAuth = false;
                originalRequest._cookieRetried = true;
                return api(originalRequest);
            }
            // If we're already refreshing, queue this request
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                }).then(() => {
                    // Retry original request
                    return api(originalRequest);
                }).catch(err => {
                    return Promise.reject(err);
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                // Attempt to refresh the session using our centralized function
                const newSession = await refreshSession();

                if (newSession?.accessToken) {
                    // Update the authorization header for the retry
                    originalRequest.headers.Authorization = `Bearer ${newSession.accessToken}`;

                    processQueue(null, newSession.accessToken);
                    isRefreshing = false;

                    console.log('[AUTH] Token refreshed successfully, retrying request');

                    // Retry the original request
                    return api(originalRequest);
                }

                // If we get here, session refresh failed
                console.warn('[AUTH] Token refresh failed, session may have expired');
                processQueue(new Error('Token refresh failed'), null);
                isRefreshing = false;

                // Check if we're in a browser environment before redirecting
                if (typeof window !== 'undefined') {
                    console.log('[AUTH] Redirecting to sign in');
                    // Clear any stale session data before redirecting
                    await fetch('/api/auth/signout', { method: 'POST', credentials: 'include' });
                    window.location.href = '/api/auth/signin';
                }

            } catch (refreshError) {
                console.warn('[AUTH] Error during token refresh:', refreshError);
                processQueue(refreshError, null);
                isRefreshing = false;

                // Check if we're in a browser environment before redirecting
                if (typeof window !== 'undefined') {
                    console.log('[AUTH] Token refresh failed, redirecting to sign in');
                    // Clear any stale session data before redirecting
                    try {
                        await fetch('/api/auth/signout', { method: 'POST', credentials: 'include' });
                    } catch (signoutError) {
                        console.warn('[AUTH] Failed to sign out:', signoutError);
                    }
                    window.location.href = '/api/auth/signin';
                }
            }
        }

        return Promise.reject(error);
    }
);

export default api;
