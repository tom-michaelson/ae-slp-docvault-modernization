import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from '@pages/base/BasePage';
import { testId } from '@constants';
import { ElementHelpers } from '@helpers/ElementHelpers';
import { WaitHelpers } from '@helpers/WaitHelpers';

/**
 * Page object for Workflow Listing interactions
 */
export class WorkflowListing extends BasePage {
    readonly runListingContainer: Locator;
    readonly statusBadges: Locator;

    constructor(page: Page) {
        super(page);
        this.runListingContainer = page.locator(`[data-testid^="${testId.listing.runListing}"]`);
        this.statusBadges = page.locator(`[data-testid^="${testId.statusBadge.badge}"]`);
    }

    /**
     * Check if the workflow listing is loaded
     */
    async isLoaded(): Promise<boolean> {
        try {
            // Check if table exists - it should exist even if empty
            const tableExists = await this.page.locator('table').isVisible();
            return tableExists;
        } catch {
            return false;
        }
    }

    /**
     * Get expected URL pattern - listing typically appears on runs page
     */
    getExpectedUrlPattern(): RegExp {
        return /.*\/runs/;
    }

    /**
     * Get all workflow runs
     */
    async getAllRuns(): Promise<Locator[]> {
        const runs = await this.runListingContainer.all();
        return runs;
    }

    /**
     * Get run by ID
     */
    async getRunById(runId: string): Promise<Locator> {
        return this.page.getByTestId(`${testId.listing.runListing}-${runId}`);
    }

    /**
     * Click on a specific run table row
     */
    async clickRun(runId: string): Promise<void> {
        const runLocator = await this.getRunById(runId);
        await ElementHelpers.waitAndClick(runLocator);
    }

    /**
     * Get status of a specific run
     */
    async getRunStatus(runId: string): Promise<string | null> {
        const runLocator = await this.getRunById(runId);
        const statusBadge = runLocator.locator(`[data-testid^="${testId.statusBadge}"]`);
        return await ElementHelpers.getTextSafe(statusBadge);
    }

    /**
     * Wait for run to appear in listing
     */
    async waitForRun(runId: string, timeout: number = 30000): Promise<void> {
        const runLocator = await this.getRunById(runId);
        await this.waitForElementVisible(runLocator, timeout);
    }

    /**
     * Wait for run status to change
     */
    async waitForRunStatus(
        runId: string,
        expectedStatus: string,
        timeout: number = 60000
    ): Promise<void> {
        await WaitHelpers.retry(
            async () => {
                const status = await this.getRunStatus(runId);
                if (status?.toLowerCase() !== expectedStatus.toLowerCase()) {
                    throw new Error(`Status is ${status}, expected ${expectedStatus}`);
                }
            },
            Math.floor(timeout / 1000),
            1000
        );
    }

    /**
     * Get all run statuses
     */
    async getAllRunStatuses(): Promise<string[]> {
        return await ElementHelpers.getAllTexts(this.statusBadges);
    }

    /**
     * Filter runs by status
     */
    async filterByStatus(status: string): Promise<Locator[]> {
        const allRuns = await this.getAllRuns();
        const filteredRuns: Locator[] = [];

        for (const run of allRuns) {
            const runStatus = await ElementHelpers.getTextSafe(
                run.locator(`[data-testid^="${testId.statusBadge}"]`)
            );
            if (runStatus?.toLowerCase() === status.toLowerCase()) {
                filteredRuns.push(run);
            }
        }

        return filteredRuns;
    }

    /**
     * Get count of runs with specific status
     */
    async getStatusCount(status: string): Promise<number> {
        const filteredRuns = await this.filterByStatus(status);
        return filteredRuns.length;
    }

    /**
     * Check if listing is empty
     */
    async isEmpty(): Promise<boolean> {
        const runs = await this.getAllRuns();
        return runs.length === 0;
    }

    /**
     * Expect run to be in listing
     */
    async expectRunInListing(runId: string): Promise<void> {
        const runLocator = await this.getRunById(runId);
        await expect(runLocator).toBeVisible();
    }

    /**
     * Expect run to have status
     */
    async expectRunStatus(runId: string, expectedStatus: string): Promise<void> {
        const status = await this.getRunStatus(runId);
        expect(status?.toLowerCase()).toBe(expectedStatus.toLowerCase());
    }

    /**
     * Get run details from table row
     */
    async getRunDetails(runId: string): Promise<Record<string, string>> {
        const runLocator = await this.getRunById(runId);
        const details: Record<string, string> = {};

        // Extract details from table cells (td elements)
        const cells = await runLocator.locator('td').all();

        if (cells.length >= 5) {
            // Based on WorkflowListing component structure:
            // td[0] = workflow type
            // td[1] = status badge
            // td[2] = duration
            // td[3] = started timestamp
            // td[4] = monitor link
            details.workflowType = await ElementHelpers.getTextSafe(cells[0]) || '';
            details.status = await ElementHelpers.getTextSafe(cells[1]) || '';
            details.duration = await ElementHelpers.getTextSafe(cells[2]) || '';
            details.startTime = await ElementHelpers.getTextSafe(cells[3]) || '';

            // Get monitor link href
            const monitorLink = cells[4].locator('a');
            if (await ElementHelpers.exists(monitorLink)) {
                details.monitorUrl = await monitorLink.getAttribute('href') || '';
            }
        }

        return details;
    }

    /**
     * Refresh the listing
     */
    async refresh(): Promise<void> {
        await this.reload();
        await this.waitForPageReady();
        await this.waitForListingReady();
    }

    /**
     * Wait for listing to load
     */
    async waitForListingReady(): Promise<void> {
        // Wait for the table structure to be visible
        const tableSelector = 'table';
        await this.page.waitForSelector(tableSelector, { state: 'visible' });

        // Wait for at least one workflow run row to be present (ignoring the UUID in data-testid)
        const workflowRowSelector = `tr[data-testid*="${testId.listing.runListing}-"]`;
        await this.page.waitForSelector(workflowRowSelector, { state: 'visible' });
        await this.waitForNetworkIdle();
    }
}
