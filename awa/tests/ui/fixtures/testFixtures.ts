import { test as base, Page } from '@playwright/test';
import {
    HomePage,
    RunsPage,
    WorkflowPanel,
    WorkflowModal,
    WorkflowListing
} from '@pages/index';
import { TestDataHelpers } from '@helpers/TestDataHelpers';
import { AuthHelpers } from '@helpers/auth/AuthHelpers';
import { testId } from '@constants';

/**
 * Custom page object fixtures
 */
type PageObjects = {
    homePage: HomePage;
    runsPage: RunsPage;
    workflowPanel: WorkflowPanel;
    workflowModal: WorkflowModal;
    workflowListing: WorkflowListing;
};

/**
 * Test data fixtures
 */
type TestData = {
    testRunId: string;
    testWorkflowName: string;
    testWorkflowInput: string;
};

/**
 * Test cleanup tracking
 */
type CleanupData = {
    createdWorkflowIds: string[];
    openModals: boolean;
};

/**
 * Combined fixtures type
 */
type TestFixtures = PageObjects & TestData & {
    authenticatedPage: Page;
    cleanupData: CleanupData;
    autoCleanup: void;
};

/**
 * Extended test with custom fixtures
 */
export const test = base.extend<TestFixtures>({
    // Page object fixtures
    homePage: async ({ page }, use) => {
        const homePage = new HomePage(page);
        await use(homePage);
    },

    runsPage: async ({ page }, use) => {
        const runsPage = new RunsPage(page);
        await use(runsPage);
    },

    workflowPanel: async ({ page }, use) => {
        const workflowPanel = new WorkflowPanel(page);
        await use(workflowPanel);
    },

    workflowModal: async ({ page }, use) => {
        const workflowModal = new WorkflowModal(page);
        await use(workflowModal);
    },

    workflowListing: async ({ page }, use) => {
        const workflowListing = new WorkflowListing(page);
        await use(workflowListing);
    },

    // Test data fixtures
    testRunId: async ({}, use) => {
        await use(TestDataHelpers.generateId());
    },

    testWorkflowName: async ({}, use) => {
        await use(TestDataHelpers.generateWorkflowName());
    },

    testWorkflowInput: async ({}, use) => {
        await use(TestDataHelpers.generateWorkflowInput());
    },

    // Cleanup data fixture
    cleanupData: async ({}, use) => {
        const data: CleanupData = {
            createdWorkflowIds: [],
            openModals: false
        };
        await use(data);
    },

    // Authenticated page fixture
    authenticatedPage: async ({ page }, use) => {
        // Use AuthHelpers for login
        await AuthHelpers.login(page);
        await use(page);
    },

    // Automatic cleanup fixture
    autoCleanup: [async ({ page, cleanupData }, use) => {
        // Test runs here
        await use();

        // Cleanup after test
        try {
            // Close any open modals
            const modalCloseButton = page.getByTestId(testId.modal.closeButton);
            if (await modalCloseButton.isVisible({ timeout: 1000 })) {
                await modalCloseButton.click();
                await page.waitForTimeout(500);
            }

            // Clear browser storage (keep lightweight for all tests)
            try {
                await page.evaluate(() => {
                    localStorage.clear();
                    sessionStorage.clear();
                });
            } catch {
                // Ignore localStorage errors (e.g., about:blank or file:// pages)
            }

            // Navigate away from current page to reset state
            await page.goto('about:blank');

            // Log cleanup summary
            if (cleanupData.createdWorkflowIds.length > 0) {
                console.log(`Test cleanup: Created ${cleanupData.createdWorkflowIds.length} workflow(s)`);
            }
        } catch (error) {
            console.error('Cleanup error:', error);
        }
    }, { auto: true }],
});

/**
 * Re-export expect for convenience
 */
export { expect } from '@playwright/test';

/**
 * Test hooks for common setup/teardown
 */
export const hooks = {
    /**
     * Before each test hook for authenticated tests
     */
    beforeEachAuthenticated: async ({ authenticatedPage }: TestFixtures) => {
        // Page is already authenticated
        await authenticatedPage.waitForLoadState('networkidle');
    },

    /**
     * After each test hook for cleanup
     */
    afterEachCleanup: async ({ page }: { page: Page }) => {
        // Use AuthHelpers for logout/cleanup
        await AuthHelpers.logout(page);
    },
};

/**
 * Common test scenarios as reusable functions
 */
export const scenarios = {
    /**
     * Login flow
     */
    login: async (page: Page, options?: { clearSession?: boolean }) => {
        // Clear session state if requested (for authentication tests)
        if (options?.clearSession) {
            await page.context().clearCookies();

            try {
                await page.evaluate(() => {
                    localStorage.clear();
                    sessionStorage.clear();
                });
            } catch {
                // Ignore localStorage errors (e.g., about:blank page)
            }
        }

        // Use AuthHelpers for consistent login
        await AuthHelpers.login(page);
    },

    /**
     * Create and execute workflow
     */
    createWorkflowRun: async (
        runsPage: RunsPage,
        workflowModal: WorkflowModal,
        workflowName: string = 'test-workflow'
    ) => {
        await runsPage.clickNewRunButton();
        await workflowModal.waitForModalOpen();
        await workflowModal.selectWorkflowByType(workflowName, { name: 'Test User' });
        await workflowModal.waitForExecuteButtonEnabled();
        await workflowModal.execute();
    },

    /**
     * Wait for workflow completion
     */
    waitForWorkflowComplete: async (
        workflowListing: WorkflowListing,
        runId: string,
        expectedStatus: string = 'completed'
    ) => {
        await workflowListing.waitForRun(runId);
        await workflowListing.waitForRunStatus(runId, expectedStatus);
    },
};
