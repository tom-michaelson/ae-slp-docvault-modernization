import { test, expect, scenarios } from '@fixtures/testFixtures';

test.describe('Homepage Tests', () => {
  test('Page Title is correct', async ({ homePage }) => {
    await homePage.goto();
    await homePage.expectPageTitle();
  });

  test('Welcome Message appears', async ({ homePage }) => {
    await homePage.goto();
    await homePage.expectWelcomeMessage();
  });
});

test.describe('Authentication Flow', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('Complete login flow', async ({ page }) => {
    await scenarios.login(page, { clearSession: true });
    await expect(page).toHaveURL(/.*\/runs/);
  });
});

test.describe('Workflow Execution', () => {
  test('Create and execute workflow', async ({
    authenticatedPage,
    runsPage,
    workflowModal,
    workflowPanel
  }) => {
    // Navigate to runs page
    await runsPage.goto();
    await runsPage.expectRunsPage();

    // Open new workflow modal
    await workflowPanel.clickNewRun();
    await workflowModal.waitForModalOpen();

    // Select and execute workflow
    await workflowModal.selectWorkflowByType('awa-hello-world', { name: 'Test User' });
    await workflowModal.waitForExecuteButtonEnabled();
    await workflowModal.execute();

    // Verify modal closed
    await workflowModal.expectModalClosed();
  });

});

test.describe('Workflow Listing', () => {
  test('View workflow runs', async ({
    authenticatedPage,
    runsPage,
    workflowListing,
    workflowModal
  }) => {
    await runsPage.goto();

    // Create a workflow run first to ensure listing has data
    await scenarios.createWorkflowRun(runsPage, workflowModal, 'awa-hello-world');

    // Wait for listing to show the run
    await workflowListing.waitForListingReady();

    // Verify the listing has runs
    const isEmpty = await workflowListing.isEmpty();
    expect(isEmpty).toBe(false);

    const statuses = await workflowListing.getAllRunStatuses();
    expect(statuses.length).toBeGreaterThan(0);
  });
});
