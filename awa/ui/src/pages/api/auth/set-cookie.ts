import type { APIRoute } from 'astro';
import { getSession } from 'auth-astro/server';

// Disable prerendering for this API route
export const prerender = false;

export const POST: APIRoute = async ({ request, cookies }) => {
  try {
    // Get the current session
    const session = await getSession(request);

    console.log('[AUTH] Set-cookie endpoint called, session:', session ? 'found' : 'not found');

    if (!session?.accessToken) {
      console.error('[AUTH] No accessToken in session:', session);
      return new Response(JSON.stringify({ error: 'No access token in session' }), {
        status: 401,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }

    // Set the JWT token as an httpOnly cookie
    cookies.set('awa_auth_token', session.accessToken as string, {
      httpOnly: true,
      secure: import.meta.env.PROD, // Only use secure in production
      sameSite: 'lax',
      path: '/',
      // Set expiry based on token expiry
      maxAge: 60 * 60 * 24, // 24 hours (adjust based on your token expiry)
    });

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('[AUTH] Error setting cookie:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
};
