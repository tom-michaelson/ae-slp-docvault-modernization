import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from '@pages/base/BasePage';
import { testId } from '@constants';
import { WaitHelpers } from '@helpers/WaitHelpers';
import { ElementHelpers } from '@helpers/ElementHelpers';
import { ModalHelpers } from '@helpers/modal/ModalHelpers';

export class RunsPage extends BasePage {
    readonly runsList: Locator;
    readonly newRunButton: Locator;
    readonly workflowSelect: Locator;
    readonly executeButton: Locator;
    readonly runStatusBadge: Locator;
    private modalHelpers: ModalHelpers;

    constructor(page: Page) {
        super(page);
        this.runsList = page.locator('[data-testid="runs-list"]');
        this.newRunButton = page.getByTestId(testId.panel.newRunButton);
        this.workflowSelect = page.getByTestId(testId.modal.workflowSelect);
        this.executeButton = page.getByTestId(testId.modal.executeButton);
        this.runStatusBadge = page.getByTestId('run-status');
        this.modalHelpers = new ModalHelpers(page);
    }

    /**
     * Check if the runs page is loaded
     */
    async isLoaded(): Promise<boolean> {
        try {
            // Check for the new run button as primary indicator
            const hasNewRunButton = await this.isElementVisible(this.newRunButton);
            // Check URL contains /runs
            const isRunsUrl = this.page.url().includes('/runs');

            return hasNewRunButton && isRunsUrl;
        } catch {
            return false;
        }
    }

    /**
     * Get expected URL pattern for runs page
     */
    getExpectedUrlPattern(): RegExp {
        return /.*\/runs/;
    }

    async goto(): Promise<void> {
        await this.navigateTo('/runs');
    }

    async expectPageTitle(): Promise<void> {
        await this.expectTitleContains('Runs');
    }

    async expectRunsPage(): Promise<void> {
        await this.expectUrlPattern(/.*\/runs/);
    }

    async clickNewRunButton(): Promise<void> {
        await this.waitForElementVisible(this.newRunButton);
        await this.safeClick(this.newRunButton);
    }

    async clickWorkflowSelect(): Promise<void> {
        await this.waitForElementVisible(this.workflowSelect);
        await this.safeClick(this.workflowSelect);
    }

    async selectWorkflowOption(option: string): Promise<void> {
        const optionLocator = this.page.getByTestId(`workflow-option-${option}`);
        await this.waitForElementVisible(optionLocator);
        await this.safeClick(optionLocator);
    }

    async clickExecuteButton(): Promise<void> {
        await this.waitForElementVisible(this.executeButton);
        await ElementHelpers.waitAndClick(this.executeButton);
    }

    async closeModal(): Promise<void> {
        await this.modalHelpers.closeModal();
    }

    async expectRunInList(runId: string): Promise<void> {
        await WaitHelpers.waitForText(this.runsList, runId);
        await expect(this.runsList).toContainText(runId);
    }

    async clickRunInList(runId: string): Promise<void> {
        const runLocator = this.page.getByTestId(`run-${runId}`);
        await ElementHelpers.waitAndClick(runLocator);
    }

    async expectRunStatus(status: string): Promise<void> {
        await expect(this.runStatusBadge).toContainText(status);
    }

    async waitForRunCompletion(timeout: number = 60000): Promise<void> {
        await WaitHelpers.retry(
            async () => {
                const status = await ElementHelpers.getTextSafe(this.runStatusBadge);
                if (status?.toLowerCase().includes('running')) {
                    throw new Error('Still running');
                }
            },
            Math.floor(timeout / 1000),
            1000
        );
    }

    async getRunStatus(): Promise<string | null> {
        return await ElementHelpers.getTextSafe(this.runStatusBadge);
    }

    async isModalOpen(): Promise<boolean> {
        return await this.modalHelpers.isModalOpen();
    }
}
