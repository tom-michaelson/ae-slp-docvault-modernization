# Capture API Traffic from Legacy Passage Page

You are capturing all REST API traffic from a legacy Passage page by navigating it with Playwright and intercepting responses. You will follow a pre-built navigation plan.

## Arguments

`$ARGUMENTS` is a JSON string with:
- `pageKey` — page directory key (e.g., `2014-line`)
- `navigationPlanFile` — path to the navigation plan JSON from Phase 1
- `outputFile` — path to write the raw API traffic JSON

Parse it: `const args = JSON.parse('$ARGUMENTS')`

## CRITICAL: Single-Call Capture Pattern

The Playwright MCP `browser_run_code` tool executes each call in its own async context.
`page.on('response')` listeners with `await response.text()` do NOT work across separate
`browser_run_code` calls — the async callbacks silently fail and the captured array stays empty.

**The fix:** The interceptor setup, ALL navigation/interaction steps, and traffic extraction MUST
happen in a SINGLE `browser_run_code` call. Login happens in a separate call beforehand (no
capture needed for login traffic).

## Steps

### Step 0: Read Navigation Plan

Read the navigation plan file at `{args.navigationPlanFile}`. Parse the JSON to get:
- `menuPath` — e.g., `"Infrastructure > Company > Company Contact"`
- `steps` — ordered interaction steps (each has `stepNumber`, `action`, `target`, `capturePhase`, `description`)
- `features` — UI feature keys for this page

### Step 1: Login to Legacy Passage

Read the login script at `.claude/tools/playwright/passage-login-v2.js` and execute it using `mcp__playwright__browser_run_code`.

After login completes, take a `mcp__playwright__browser_snapshot` to verify the main menu is visible. If the menu is NOT visible (e.g., login form still showing), wait 5 more seconds and retry the snapshot. If login clearly failed, stop and report the error.

### Step 2: Navigate Menu (except last item)

Split the `menuPath` by ` > ` to get the menu levels (e.g., `["Infrastructure", "Company", "Company Contact"]`).

Click through all menu levels EXCEPT the last one using individual `mcp__playwright__browser_run_code` calls:

```javascript
const frame = page.frameLocator('iframe').first();
await frame.getByText('{menuLevel}', { exact: true }).click();
await page.waitForTimeout(2000);
'{menuLevel} clicked';
```

Do this for each level except the final one. The final menu click loads the actual page and triggers API calls — that must happen inside the capture call (Step 3).

### Step 3: Capture Traffic (SINGLE browser_run_code call)

This is the core step. Build ONE `mcp__playwright__browser_run_code` call that does everything:
1. Registers the response interceptor
2. Clicks the LAST menu item (triggers page-load API calls)
3. Executes each interaction step from the navigation plan
4. Waits for async callbacks to complete
5. Returns the captured traffic

Use this template — adapt the menu click and interaction steps based on the navigation plan:

```javascript
async (page) => {
  // --- Register Interceptor ---
  const capturedTraffic = [];
  let currentPhase = 'page-load';

  page.on('response', async (response) => {
    const url = response.url();
    if (!url.includes('/service/')) return;

    try {
      const request = response.request();

      // Parse request body
      let requestBody = null;
      try {
        const postData = request.postData();
        if (postData) requestBody = JSON.parse(postData);
      } catch (e) {}

      // Parse response body (must await — this is why everything must be in one call)
      let responseBody = null;
      let truncated = false;
      try {
        const bodyText = await response.text();
        if (bodyText.length > 100000) {
          responseBody = JSON.parse(bodyText.substring(0, 100000));
          truncated = true;
        } else {
          responseBody = JSON.parse(bodyText);
        }
      } catch (e) {}

      // Extract endpoint — regex handles session-hash URLs like /passage3f3a.../service/...
      const urlObj = new URL(url);
      const endpoint = urlObj.pathname.replace(/^\/passage[^/]*\//, '');

      // Extract method name — legacy body structure is {data: {methodName: "..."}}
      let methodName = null;
      if (requestBody?.data?.methodName) {
        methodName = requestBody.data.methodName;
      } else if (requestBody?.method) {
        methodName = requestBody.method;
      }

      capturedTraffic.push({
        endpoint,
        methodName,
        httpMethod: request.method(),
        capturePhase: currentPhase,
        request: { url, body: requestBody },
        response: { status: response.status(), body: responseBody, truncated },
      });
    } catch (e) {
      // Skip entries that fail — don't abort the session
    }
  });

  const frame = page.frameLocator('iframe').first();

  // --- Click Last Menu Item (triggers page-load API calls) ---
  currentPhase = 'page-load';
  await frame.getByText('{LAST_MENU_ITEM}', { exact: true }).click();
  await page.waitForTimeout(5000);

  // --- Execute Interaction Steps ---
  // For EACH step in the navigation plan (skip step 1 / page_load since that just happened):

  // Example for a 'retrieve' step:
  // currentPhase = 'retrieve';
  // await frame.getByRole('button', { name: 'Retrieve' }).click();
  // await page.waitForTimeout(4000);

  // Example for a 'click_tab' step:
  // currentPhase = 'tab:addresses';
  // await frame.getByText('Addresses', { exact: true }).click();
  // await page.waitForTimeout(4000);

  // --- Wait for Async Callbacks to Finish ---
  await page.waitForTimeout(3000);

  // --- Return Results ---
  return JSON.stringify({
    totalCaptured: capturedTraffic.length,
    traffic: capturedTraffic,
  });
}
```

**Adapt the template:**
- Replace `{LAST_MENU_ITEM}` with the actual last item from `menuPath`
- Replace the example interaction steps with the actual steps from the navigation plan
- Set `currentPhase` to each step's `capturePhase` value before executing the action
- Skip step 1 if its action is `page_load` (already handled by the last menu click)

**Error handling per step:**
- If a tab can't be found, wrap in try/catch, skip it, and continue to the next step
- If the Retrieve button can't be found, capture whatever traffic was collected during page load

### Step 4: Write Output

Parse the JSON string returned from Step 3. Assemble the full output JSON and write it to `{args.outputFile}`:

```json
{
  "pageKey": "{from navigation plan}",
  "menuPath": "{from navigation plan}",
  "capturedAt": "{ISO timestamp}",
  "totalApiCalls": "{number of captured calls}",
  "apiCalls": [
    {
      "endpoint": "service/company/companyContact",
      "methodName": "getCompanyContactList",
      "httpMethod": "POST",
      "capturePhase": "retrieve",
      "request": {
        "url": "http://host:port/passage.../service/...",
        "body": {"data": {"methodName": "getCompanyContactList", "args": [{}], "argTypes": ["..."]}}
      },
      "response": {
        "status": 200,
        "body": {"data": ["..."], "totalItems": 49, "type": "SUCCESS"},
        "truncated": false
      }
    }
  ]
}
```

The `capturedAt` timestamp should be the current time in ISO 8601 format.

## Important

- Do NOT click any create, modify, or delete buttons — interaction is strictly read-only
- If the legacy system is unreachable (login fails or page doesn't load), fail immediately — do not write output
- Response bodies over 100KB are automatically truncated by the interceptor
- The interceptor only captures calls to `/service/` endpoints — static assets, CSS, images are excluded
- ALL capture logic MUST be in a single browser_run_code call — see "CRITICAL" section above
