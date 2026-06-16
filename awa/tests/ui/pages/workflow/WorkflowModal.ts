import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from '@pages/base/BasePage';
import { testId } from '@constants';
import { ElementHelpers } from '@helpers/ElementHelpers';
import { WaitHelpers } from '@helpers/WaitHelpers';

/**
 * Page object for Workflow Modal interactions
 */
export class WorkflowModal extends BasePage {
    readonly closeButton: Locator;
    readonly executeButton: Locator;
    readonly workflowSelect: Locator;
    readonly modalContainer: Locator;
    readonly dropdownMenu: Locator;

    constructor(page: Page) {
        super(page);
        this.closeButton = page.getByTestId(testId.modal.closeButton);
        this.executeButton = page.getByTestId(testId.modal.executeButton);
        this.workflowSelect = page.getByTestId(testId.modal.workflowSelect);
        this.modalContainer = page.getByTestId(testId.modal.container);
        this.dropdownMenu = page.getByTestId(testId.modal.dropdownMenu);
    }

    /**
     * Check if the workflow modal is loaded and open
     */
    async isLoaded(): Promise<boolean> {
        try {
            const isModalVisible = await this.isElementVisible(this.modalContainer);
            const hasCloseButton = await this.isElementVisible(this.closeButton);
            const hasWorkflowSelect = await this.isElementVisible(this.workflowSelect);

            return isModalVisible && hasCloseButton && hasWorkflowSelect;
        } catch {
            return false;
        }
    }

    /**
     * Get expected URL pattern - modal can appear on various pages
     */
    getExpectedUrlPattern(): RegExp {
        return /.*/; // Modal can appear on any page
    }

    /**
     * Check if modal is open
     */
    async isOpen(): Promise<boolean> {
        return await this.isElementVisible(this.modalContainer);
    }

    /**
     * Wait for modal to open
     */
    async waitForModalOpen(): Promise<void> {
        await this.waitForElementVisible(this.modalContainer);
        await this.waitForElementVisible(this.workflowSelect);
    }

    /**
     * Close the modal
     */
    async close(): Promise<void> {
        if (await this.isOpen()) {
            await this.safeClick(this.closeButton);
            await this.waitForElementHidden(this.modalContainer);
        }
    }

    /**
     * Open the workflow dropdown menu
     */
    private async openDropdown(): Promise<void> {
        await this.waitForElementVisible(this.workflowSelect);
        await this.safeClick(this.workflowSelect.locator('input'));
        await this.waitForElementVisible(this.dropdownMenu);
    }

    /**
     * Select an option from the dropdown menu
     */
    private async selectOption(text: string, useFirst: boolean = true): Promise<void> {
        const optionLocator = this.dropdownMenu
            .locator('li[role="option"]')
            .filter({ hasText: text });
        const finalLocator = useFirst ? optionLocator.first() : optionLocator;
        await this.waitForElementVisible(finalLocator);
        await this.safeClick(finalLocator);
    }


    /**
     * Select a workflow from dropdown
     */
    async selectWorkflow(workflowName: string): Promise<void> {
        await this.openDropdown();
        await this.selectOption(workflowName);
    }


    /**
     * Select workflow by index
     */
    async selectWorkflowByIndex(index: number): Promise<void> {
        await this.openDropdown();
        const options = this.dropdownMenu.locator('li[role="option"]');
        await options.nth(index).click();
    }

    /**
     * Get selected workflow name
     */
    async getSelectedWorkflow(): Promise<string | null> {
        return await ElementHelpers.getTextSafe(this.workflowSelect);
    }

    /**
     * Execute the workflow
     */
    async execute(): Promise<void> {
        await this.waitForElementVisible(this.executeButton);
        await expect(this.executeButton).toBeEnabled();
        await this.safeClick(this.executeButton);
    }

    /**
     * Fill workflow input (if input field exists)
     */
    async fillWorkflowInput(input: string): Promise<void> {
        const inputField = this.page.locator('[data-testid="workflow-input"]');
        if (await ElementHelpers.exists(inputField)) {
            await this.fillInput(inputField, input);
        }
    }

    /**
     * Check if execute button is enabled
     */
    async isExecuteButtonEnabled(): Promise<boolean> {
        return await this.isElementEnabled(this.executeButton);
    }

    /**
     * Wait for execute button to be enabled
     */
    async waitForExecuteButtonEnabled(): Promise<void> {
        await WaitHelpers.retry(
            async () => {
                const isEnabled = await this.isExecuteButtonEnabled();
                if (!isEnabled) {
                    throw new Error('Execute button not enabled');
                }
            },
            10,
            500
        );
    }

    /**
     * Expect modal to be open
     */
    async expectModalOpen(): Promise<void> {
        await expect(this.modalContainer).toBeVisible();
    }

    /**
     * Expect modal to be closed
     */
    async expectModalClosed(): Promise<void> {
        await expect(this.modalContainer).not.toBeVisible();
    }

    /**
     * Get all available workflow options
     */
    async getAvailableWorkflows(): Promise<string[]> {
        await this.openDropdown();

        const options = this.dropdownMenu.locator('li[role="option"]');
        const texts = await ElementHelpers.getAllTexts(options);

        // Close dropdown
        await this.page.keyboard.press('Escape');

        return texts;
    }

    /**
     * Generic method to select any workflow by type with optional input data
     */
    async selectWorkflowByType(
        workflowType: string,
        inputData?: Record<string, string>
    ): Promise<void> {
        // Select the workflow
        await this.selectWorkflow(workflowType);

        // Fill any input fields if provided
        if (inputData) {
            for (const [fieldName, value] of Object.entries(inputData)) {
                const inputSelector = `input[id="#/properties/${fieldName}-input"]`;
                const inputField = this.page.locator(inputSelector);

                if (await ElementHelpers.exists(inputField)) {
                    await this.fillInput(inputField, value);
                    // Blur the input to trigger validation and state updates
                    await inputField.blur();
                }
            }
        }
    }

    /**
     * Check if Override Defaults checkbox is visible
     */
    async hasoverrideDefaultsCheckbox(): Promise<boolean> {
        const checkbox = this.page.getByTestId(testId.modal.overrideDefaultsCheckbox);
        return await this.isElementVisible(checkbox);
    }

    /**
     * Check Override Defaults checkbox
     */
    async checkoverrideDefaults(): Promise<void> {
        const checkbox = this.page.getByTestId(testId.modal.overrideDefaultsCheckbox);
        const isChecked = await checkbox.isChecked();
        if (!isChecked) {
            await this.safeClick(checkbox);
        }
    }

    /**
     * Uncheck Override Defaults checkbox
     */
    async uncheckoverrideDefaults(): Promise<void> {
        const checkbox = this.page.getByTestId(testId.modal.overrideDefaultsCheckbox);
        const isChecked = await checkbox.isChecked();
        if (isChecked) {
            await this.safeClick(checkbox);
        }
    }

    /**
     * Check if Override Defaults checkbox is checked
     */
    async isoverrideDefaultsChecked(): Promise<boolean> {
        const checkbox = this.page.getByTestId(testId.modal.overrideDefaultsCheckbox);
        return await checkbox.isChecked();
    }
}
