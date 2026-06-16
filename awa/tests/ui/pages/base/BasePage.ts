import { Page, Locator, expect } from '@playwright/test';

/**
 * Base Page class with common functionality for all page objects
 */
export abstract class BasePage {
    protected readonly page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    /**
     * Abstract method that must be implemented by all page objects
     * Returns true if the page is loaded and ready for interaction
     */
    abstract isLoaded(): Promise<boolean>;

    /**
     * Abstract method to get the expected URL pattern for this page
     */
    abstract getExpectedUrlPattern(): RegExp;

    /**
     * Wait for the page to be loaded and ready
     * Throws an error if the page doesn't load within timeout
     */
    async waitForPageLoad(timeout: number = 30000): Promise<void> {
        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            if (await this.isLoaded()) {
                return;
            }
            await this.page.waitForTimeout(100);
        }

        throw new Error(`Page did not load within ${timeout}ms. Current URL: ${this.page.url()}`);
    }

    /**
     * Navigate to a specific path
     */
    async navigateTo(path: string): Promise<void> {
        await this.page.goto(path);
        await this.waitForPageReady();
        await this.waitForPageLoad();
    }

    /**
     * Wait for the page to be fully loaded
     */
    async waitForPageReady(): Promise<void> {
        await this.page.waitForLoadState('networkidle', { timeout: 60000 });
        await this.page.waitForLoadState('domcontentloaded');
    }

    /**
     * Wait for an element to be visible
     */
    async waitForElementVisible(locator: Locator, timeout?: number): Promise<void> {
        await locator.waitFor({ state: 'visible', timeout });
    }

    /**
     * Wait for an element to be hidden
     */
    async waitForElementHidden(locator: Locator, timeout?: number): Promise<void> {
        await locator.waitFor({ state: 'hidden', timeout });
    }

    /**
     * Wait for network to be idle
     */
    async waitForNetworkIdle(): Promise<void> {
        await this.page.waitForLoadState('networkidle');
    }

    /**
     * Check if an element is visible
     */
    async isElementVisible(locator: Locator): Promise<boolean> {
        return await locator.isVisible();
    }

    /**
     * Check if an element is enabled
     */
    async isElementEnabled(locator: Locator): Promise<boolean> {
        return await locator.isEnabled();
    }

    /**
     * Take a screenshot with a descriptive name
     */
    async takeScreenshot(name: string): Promise<void> {
        await this.page.screenshot({
            path: `tests/ui/screenshots/${name}-${Date.now()}.png`,
            fullPage: true
        });
    }

    /**
     * Assert URL matches a pattern
     */
    async expectUrlPattern(pattern: RegExp): Promise<void> {
        await expect(this.page).toHaveURL(pattern);
    }

    /**
     * Assert page title contains text
     */
    async expectTitleContains(text: string): Promise<void> {
        await expect(this.page).toHaveTitle(new RegExp(text));
    }

    /**
     * Get current URL
     */
    getUrl(): string {
        return this.page.url();
    }

    /**
     * Reload the current page
     */
    async reload(): Promise<void> {
        await this.page.reload();
        await this.waitForPageReady();
    }

    /**
     * Safe click with retry logic and navigation detection
     */
    async safeClick(locator: Locator, retries: number = 3): Promise<void> {
        const initialUrl = this.page.url();

        for (let i = 0; i < retries; i++) {
            try {
                await locator.click({ timeout: 5000 });
                return;
            } catch (error) {
                // Check if URL changed (navigation success despite click error)
                if (this.page.url() !== initialUrl) {
                    return;
                }

                if (i === retries - 1) throw error;
                await this.page.waitForTimeout(1000);
            }
        }
    }

    /**
     * Fill input with clear first
     */
    async fillInput(locator: Locator, value: string): Promise<void> {
        await locator.clear();
        await locator.fill(value);
    }

    /**
     * Scroll element into view
     */
    async scrollIntoView(locator: Locator): Promise<void> {
        await locator.scrollIntoViewIfNeeded();
    }

    /**
     * Wait for a specific timeout
     */
    async wait(milliseconds: number): Promise<void> {
        await this.page.waitForTimeout(milliseconds);
    }
}
