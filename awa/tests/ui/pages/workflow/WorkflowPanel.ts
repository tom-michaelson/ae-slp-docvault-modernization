import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from '@pages/base/BasePage';
import { testId } from '@constants';
import { ElementHelpers } from '@helpers/ElementHelpers';

/**
 * Page object for Workflow Panel interactions
 */
export class WorkflowPanel extends BasePage {
    readonly newRunButton: Locator;

    constructor(page: Page) {
        super(page);
        this.newRunButton = page.getByTestId(testId.panel.newRunButton);
    }

    /**
     * Check if the workflow panel is loaded
     */
    async isLoaded(): Promise<boolean> {
        try {
            return await this.isElementVisible(this.newRunButton);
        } catch {
            return false;
        }
    }

    /**
     * Get expected URL pattern - panel can appear on various pages
     */
    getExpectedUrlPattern(): RegExp {
        return /.*/; // Panel can appear on any page
    }

    /**
     * Click the new run button
     */
    async clickNewRun(): Promise<void> {
        await this.waitForElementVisible(this.newRunButton);
        await this.safeClick(this.newRunButton);
    }

    /**
     * Check if new run button is enabled
     */
    async isNewRunButtonEnabled(): Promise<boolean> {
        return await this.isElementEnabled(this.newRunButton);
    }

    /**
     * Check if panel is visible
     */
    async isPanelVisible(): Promise<boolean> {
        return await this.isElementVisible(this.newRunButton);
    }

    /**
     * Wait for panel to be ready
     */
    async waitForPanelReady(): Promise<void> {
        await this.waitForElementVisible(this.newRunButton);
        await this.waitForNetworkIdle();
    }

    /**
     * Expect new run button to be visible
     */
    async expectNewRunButtonVisible(): Promise<void> {
        await expect(this.newRunButton).toBeVisible();
    }

    /**
     * Expect new run button to be enabled
     */
    async expectNewRunButtonEnabled(): Promise<void> {
        await expect(this.newRunButton).toBeEnabled();
    }
}
