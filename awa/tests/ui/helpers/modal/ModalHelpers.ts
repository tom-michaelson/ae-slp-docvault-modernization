import { Page, Locator } from '@playwright/test';
import { testId } from '@constants';
import { ElementHelpers } from '@helpers/ElementHelpers';

/**
 * Common modal helper utilities
 */
export class ModalHelpers {
    private readonly page: Page;
    private readonly modalContainer: Locator;
    private readonly closeButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.modalContainer = page.getByTestId(testId.modal.container);
        this.closeButton = page.getByTestId(testId.modal.closeButton);
    }

    /**
     * Check if any modal is currently open
     */
    async isModalOpen(): Promise<boolean> {
        return await this.modalContainer.isVisible();
    }

    /**
     * Wait for a modal to open
     */
    async waitForModalOpen(timeout: number = 30000): Promise<void> {
        await this.modalContainer.waitFor({ state: 'visible', timeout });
    }

    /**
     * Wait for modal to close
     */
    async waitForModalClosed(timeout: number = 30000): Promise<void> {
        await this.modalContainer.waitFor({ state: 'hidden', timeout });
    }

    /**
     * Close the currently open modal
     */
    async closeModal(): Promise<void> {
        if (await this.isModalOpen()) {
            await this.closeButton.click();
            await this.waitForModalClosed();
        }
    }

    /**
     * Get modal title text
     */
    async getModalTitle(): Promise<string | null> {
        const titleLocator = this.modalContainer.locator('h2, h3').first();
        return await ElementHelpers.getTextSafe(titleLocator);
    }

    /**
     * Check if a specific element exists within the modal
     */
    async hasElementInModal(selector: string): Promise<boolean> {
        const element = this.modalContainer.locator(selector);
        return await ElementHelpers.exists(element);
    }

    /**
     * Click an element within the modal
     */
    async clickElementInModal(selector: string): Promise<void> {
        const element = this.modalContainer.locator(selector);
        await element.click();
    }
}
