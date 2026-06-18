import { Locator } from '@playwright/test';

/**
 * Custom wait utilities for complex scenarios
 */
export class WaitHelpers {
    /**
     * Wait for text to appear in element
     */
    static async waitForText(
        locator: Locator,
        text: string,
        timeout: number = 30000
    ): Promise<void> {
        await locator.filter({ hasText: text }).waitFor({ state: 'visible', timeout });
    }

    /**
     * Custom retry mechanism
     */
    static async retry<T>(
        fn: () => Promise<T>,
        retries: number = 3,
        delay: number = 1000
    ): Promise<T> {
        let lastError: Error;

        for (let i = 0; i < retries; i++) {
            try {
                return await fn();
            } catch (error) {
                lastError = error as Error;
                if (i < retries - 1) {
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }

        throw lastError!;
    }
}
