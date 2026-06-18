import { Locator } from '@playwright/test';

/**
 * Helper utilities for element interactions
 */
export class ElementHelpers {
    /**
     * Check if element exists in DOM
     */
    static async exists(locator: Locator): Promise<boolean> {
        return await locator.count() > 0;
    }

    /**
     * Get element text content safely
     */
    static async getTextSafe(locator: Locator): Promise<string | null> {
        try {
            return await locator.textContent();
        } catch {
            return null;
        }
    }

    /**
     * Get all texts from multiple elements
     */
    static async getAllTexts(locator: Locator): Promise<string[]> {
        return await locator.allTextContents();
    }


    /**
     * Get attribute value
     */
    static async getAttribute(locator: Locator, name: string): Promise<string | null> {
        return await locator.getAttribute(name);
    }

    /**
     * Wait and click
     */
    static async waitAndClick(locator: Locator, timeout: number = 30000): Promise<void> {
        await locator.waitFor({ state: 'visible', timeout });
        await locator.click();
    }


    /**
     * Get element count
     */
    static async getCount(locator: Locator): Promise<number> {
        return await locator.count();
    }

}
