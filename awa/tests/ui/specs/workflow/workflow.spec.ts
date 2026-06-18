import { test, expect, scenarios, hooks } from '@fixtures/testFixtures';
import { TestDataHelpers } from '@helpers/TestDataHelpers';
import { testId } from '@constants';

test.describe('Workflow End-to-End Tests', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await hooks.beforeEachAuthenticated({ authenticatedPage });
  });

  test.afterEach(async ({ page }) => {
    await hooks.afterEachCleanup({ page });
  });

  test('Complete workflow lifecycle', async ({
    runsPage,
    workflowPanel,
    workflowModal,
    workflowListing,
    testRunId
  }) => {
    test.setTimeout(120000); // 2 minutes for workflow execution and monitoring
    // Step 1: Navigate to runs page
    await test.step('Navigate to runs page', async () => {
      await runsPage.goto();
      await runsPage.expectRunsPage();
    });

    // Step 2: Create new workflow
    await test.step('Create new workflow', async () => {
      await workflowPanel.expectNewRunButtonVisible();
      await workflowPanel.clickNewRun();
      await workflowModal.expectModalOpen();
    });

    // Step 3: Configure workflow
    await test.step('Configure workflow', async () => {
      const availableWorkflows = await workflowModal.getAvailableWorkflows();
      expect(availableWorkflows.length).toBeGreaterThan(0);

      // Select awa-hello-human workflow and fill Name input
      await workflowModal.selectWorkflowByType('awa-hello-world', { name: 'Test User' });
      await workflowModal.waitForExecuteButtonEnabled();
    });

    // Step 4: Execute workflow
    await test.step('Execute workflow', async () => {
      await workflowModal.execute();
      await workflowModal.expectModalClosed();
    });

    // Step 5: Verify workflow appears in listing
    await test.step('Verify workflow appears in listing', async () => {
      await workflowListing.waitForListingReady();

      // Get the most recent run
      const allRuns = await workflowListing.getAllRuns();
      expect(allRuns.length).toBeGreaterThan(0);

      // Get workflow statuses - should have at least one with a valid status
      const statuses = await workflowListing.getAllRunStatuses();
      expect(statuses.length).toBeGreaterThan(0);

      // Verify at least one status is set (not empty)
      const hasValidStatus = statuses.some(status => status && status.trim().length > 0);
      expect(hasValidStatus).toBe(true);
    });
  });

  test('Workflow details inspection', async ({
    runsPage,
    workflowListing,
    workflowModal,
    workflowPanel
  }) => {
    await runsPage.goto();

    // Create a new workflow run
    await scenarios.createWorkflowRun(runsPage, workflowModal, 'awa-hello-world');

    // Wait for it to appear in listing
    await workflowListing.waitForListingReady();
    const allRuns = await workflowListing.getAllRuns();
    expect(allRuns.length).toBeGreaterThan(0);

    // Get details of the first run
    const firstRun = allRuns[0];
    const runId = await firstRun.getAttribute('data-testid');
    expect(runId).toBeTruthy();

    const cleanRunId = runId!.replace(`${testId.listing.runListing}-`, '');
    const details = await workflowListing.getRunDetails(cleanRunId);

    // Verify workflow details structure
    expect(details).toHaveProperty('workflowType');
    expect(details).toHaveProperty('status');
    expect(details).toHaveProperty('duration');
    expect(details).toHaveProperty('startTime');
    expect(details.workflowType).toBeTruthy();
    expect(details.status).toBeTruthy();

    // If monitor URL exists, verify it's a valid URL
    if (details.monitorUrl) {
      expect(details.monitorUrl).toMatch(/^https?:\/\//i);
    }

    // Click to view more details
    await workflowListing.clickRun(cleanRunId);

    // Wait briefly for navigation/modal/detail view
    await workflowListing.waitForNetworkIdle();
    expect(runsPage.getUrl()).toContain(`/runs/${cleanRunId}`);
  });
});
