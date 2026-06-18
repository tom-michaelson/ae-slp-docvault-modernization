import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from '@pages/base/BasePage';

export class HomePage extends BasePage {
    readonly welcomeMessage: Locator;
    readonly loginLink: Locator;
    readonly anonymousSignInButton: Locator;

    constructor(page: Page) {
        super(page);
        this.welcomeMessage = page.locator('body');
        this.loginLink = page.getByTestId('login-link');
        this.anonymousSignInButton = page.getByRole('button', { name: 'Sign in with Anonymous' });
    }

    /**
     * Check if the home page is loaded
     */
    async isLoaded(): Promise<boolean> {
        try {
            // Check for welcome message or login link
            const hasWelcomeMessage = await this.welcomeMessage.textContent()
                .then(text => text?.includes('Welcome to the Slalom Agentic Workflow Accelerator') ?? false);
            const hasLoginLink = await this.isElementVisible(this.loginLink);

            return hasWelcomeMessage || hasLoginLink;
        } catch {
            return false;
        }
    }

    /**
     * Get expected URL pattern for home page
     */
    getExpectedUrlPattern(): RegExp {
        return /^[^\/]*\/?$/; // Root URL with optional trailing slash
    }

    async goto(): Promise<void> {
        await this.navigateTo('/');
    }

    async expectWelcomeMessage(): Promise<void> {
        await expect(this.welcomeMessage).toContainText('Welcome to the Slalom Agentic Workflow Accelerator(AWA)');
    }

    async expectPageTitle(): Promise<void> {
        await this.expectTitleContains('Slalom AWA');
    }

    async clickLoginLink(): Promise<void> {
        await this.safeClick(this.loginLink);
    }

    async expectLoginUrl(): Promise<void> {
        await this.expectUrlPattern(/.*\/api\/auth\/signin/);
    }

    async clickAnonymousSignIn(): Promise<void> {
        await this.waitForElementVisible(this.anonymousSignInButton);
        await this.safeClick(this.anonymousSignInButton);
    }

    async isLoggedIn(): Promise<boolean> {
        return !(await this.isElementVisible(this.loginLink));
    }
}
