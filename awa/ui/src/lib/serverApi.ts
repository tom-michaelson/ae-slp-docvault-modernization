import axios from 'axios';
import type { Session } from '@auth/core/types';

const apiUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8001';
const authMode = import.meta.env.PUBLIC_AUTH_MODE || 'none';

/**
 * Create an API client for server-side requests with optional session
 */
export function createServerApi(session?: Session | null) {
    const api = axios.create({
        baseURL: apiUrl,
        headers: {
            'Content-Type': 'application/json',
        }
    });

    // Add auth header if in Cognito mode and session has access token
    if (authMode === 'cognito' && session?.accessToken) {
        api.defaults.headers.Authorization = `Bearer ${session.accessToken}`;
    }

    return api;
}

/**
 * Server-side API calls with session support
 */
export const serverApi = {
    async getRunningWorkflows(session?: Session | null) {
        const api = createServerApi(session);
        const { data: { workflows } } = await api.get('/api/v1/workflows/runs');
        return workflows;
    },

    async getAvailableWorkflows(session?: Session | null) {
        const api = createServerApi(session);
        const { data: { workflows } } = await api.get('/api/v1/workflows/list');
        return workflows;
    }
};
