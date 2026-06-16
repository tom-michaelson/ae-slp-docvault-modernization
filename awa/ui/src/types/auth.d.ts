// Type augmentation for auth-astro session to include tokens
declare module '@auth/core/types' {
    interface Session {
        accessToken?: string;
        idToken?: string;
    }
}

declare module '@auth/core/jwt' {
    interface JWT {
        accessToken?: string;
        idToken?: string;
    }
}

export {};
