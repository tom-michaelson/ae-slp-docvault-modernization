import { Page } from '@playwright/test';
import { HomePage } from '@pages/home';

/**
 * Authentication helper utilities
 */
export class AuthHelpers {
    /**
     * Perform login flow
     */
    static async login(page: Page): Promise<void> {
        const homePage = new HomePage(page);

        // Navigate to home
        await homePage.goto();

        // Check if already logged in
        const isLoggedIn = await homePage.isLoggedIn();

        if (!isLoggedIn) {
            // Perform login
            await homePage.clickLoginLink();
            await homePage.expectLoginUrl();
            await homePage.clickAnonymousSignIn();

            // Wait for redirect to runs page
            await page.waitForURL(/.*\/runs/);
        }
    }

    /**
     * Logout flow
     */
    static async logout(page: Page): Promise<void> {
        // Clear all browser storage including cookies
        await page.evaluate(() => {
            localStorage.clear();
            sessionStorage.clear();
        });

        // Clear all cookies for the domain
        await page.context().clearCookies();

        // Navigate to home to reset state
        await page.goto('/');
    }

    /**
     * Check if user is authenticated
     */
    static async isAuthenticated(page: Page): Promise<boolean> {
        const homePage = new HomePage(page);
        return await homePage.isLoggedIn();
    }
}
