# Take Screenshot for UI Feature

Capture browser screenshots of an eShopOnWeb UI feature in headless mode and save them to the feature's `screenshots/` folder. Screenshots are used by `analyze-ui-feature` to validate code analysis and by the development team to understand the legacy UI before rebuilding it in Angular 19.

This is a **discover-phase** command. It navigates a live eShopOnWeb instance using Playwright MCP, captures the page, and writes PNG files to `{output_dir}/`.

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
key=<feature-key>  legacy_dir=<abs-path>  url=<full-url>  output_dir=<abs-path>  marker_path=<abs-path>
```

| Argument | Description |
|---|---|
| `key` | The feature key (e.g., `basket-view-page`) |
| `legacy_dir` | Absolute path to the eShopOnWeb source root — used to read metadata if needed |
| `url` | Full URL of the feature (e.g., `http://localhost:5106/Basket`). When absent the workflow provides `file=<path>` instead — see Step 1. |
| `output_dir` | Absolute path to the screenshots output folder (e.g., `.../ui-features/basket-view-page/screenshots`) |
| `marker_path` | Absolute path to the `SCREENSHOTS_COMPLETE` marker file |

**Examples:**

```
key=basket-view-page
legacy_dir=/abs/path/target_repo/source
url=http://localhost:5106/Basket
output_dir=/abs/path/docs/entry-points/ui-features/basket-view-page/screenshots
marker_path=/abs/path/docs/entry-points/ui-features/basket-view-page/screenshots/SCREENSHOTS_COMPLETE
```

```
key=homepage-catalog-list
legacy_dir=/abs/path/target_repo/source
url=http://localhost:5106/
output_dir=/abs/path/docs/entry-points/ui-features/homepage-catalog-list/screenshots
marker_path=/abs/path/docs/entry-points/ui-features/homepage-catalog-list/screenshots/SCREENSHOTS_COMPLETE
```

```
key=admin-catalog-item-list
legacy_dir=/abs/path/target_repo/source
url=http://localhost:5106/Admin/Catalog
output_dir=/abs/path/docs/entry-points/ui-features/admin-catalog-item-list/screenshots
marker_path=/abs/path/docs/entry-points/ui-features/admin-catalog-item-list/screenshots/SCREENSHOTS_COMPLETE
```

---

## Output

```
{output_dir}/
├── {key}.png                  ← primary screenshot (initial page load)
├── {key}-{state}.png          ← additional state screenshots if captured
└── SCREENSHOTS_COMPLETE       ← timestamp marker written last
```

The `SCREENSHOTS_COMPLETE` file is a plain text file containing an ISO-8601 timestamp. The workflow uses its existence as a gate — do not create it until all screenshots have been moved into `output_dir`.

**Screenshot naming:**
- Primary screenshot: `{key}.png` (e.g., `basket-view-page.png`)
- Named states: `{key}-empty.png`, `{key}-loaded.png`, `{key}-form.png` — use when the feature has a clearly distinct meaningful alternate state (empty basket, form open, etc.)
- If in doubt, one screenshot named `{key}.png` is sufficient.

---

## Credentials

eShopOnWeb ships with two seeded accounts. Choose based on the feature's auth requirements:

| Account | Email | Password | Use for |
|---|---|---|---|
| Demo user | `demouser@microsoft.com` | `Pass@word1` | Shopping features (`/Basket`, `/`, `/Order`, checkout) |
| Admin | `admin@microsoft.com` | `Pass@word1` | Admin features (`/Admin/`, Blazor pages) |

Login form is at: `{base_url}/Identity/Account/Login`

Login form selectors (ASP.NET Identity rendered HTML):
- Email field: `id="Input_Email"` (name: `Input.Email`)
- Password field: `id="Input_Password"` (name: `Input.Password`)
- Submit button: `button[type="submit"]` with visible text "Log in"

---

## Step 1: Parse Arguments and Check Prerequisites

1. Parse all args from `{{PROMPT}}`.
2. **If no `url` arg** (only `file=` was provided): the app is not running. Write the marker with a note and stop:
   ```bash
   mkdir -p {output_dir}
   echo "SKIPPED - no running app URL provided at $(date -Iseconds)" > {marker_path}
   ```
   Report: "Skipped — no `url` argument; screenshots require a running eShopOnWeb instance."
3. **If `url` is present:** extract the base URL (scheme + host + port) for login navigation.
   Example: `http://localhost:5106/Basket` → base URL is `http://localhost:5106`
4. Check whether the `SCREENSHOTS_COMPLETE` marker already exists at `marker_path`. If it does, stop immediately — screenshots are already complete.

---

## Step 2: Read Feature Metadata

Read `docs/entry-points/ui-features/{key}/metadata.json` (relative to `cwd`, which is `target_repo/`).

Extract:
- `elementType` — to detect Blazor vs Razor Page (Blazor pages are in `/Admin/`)
- `notes` — scan for auth-related signals: look for `[Authorize]`, "requires login", "admin", "authenticated"
- `uri` — the feature's path (used to confirm which URL to navigate to)

Read `docs/entry-points/ui-features/{key}/functional-spec.md`.

Scan for:
- Auth markers: "requires authenticated", "[Authorize]", "login", "cookie" in the behavior sections
- Distinct visual states worth capturing: "empty", "no results", "form", "modal" — these become named screenshots
- Any out-of-scope notes (to avoid waiting for features that won't load)

**Auth decision logic:**
| Condition | Login as |
|---|---|
| URI starts with `/Admin/` | admin@microsoft.com |
| Notes mention "admin" or "[Authorize]" and domain = "order" or "checkout" | demouser@microsoft.com |
| Notes mention "[Authorize]" (any non-admin feature) | demouser@microsoft.com |
| No auth signals found | Skip login |

---

## Step 3: Navigate and Login (if required)

**If login is required:**

1. `mcp__playwright__browser_navigate(url="{base_url}/Identity/Account/Login")`
2. `mcp__playwright__browser_snapshot()` — verify the login form is visible
3. `mcp__playwright__browser_fill(element="Email input", ref=<ref_for_Input_Email>)` with the appropriate email
4. `mcp__playwright__browser_fill(element="Password input", ref=<ref_for_Input_Password>)` with `Pass@word1`
5. `mcp__playwright__browser_click(element="Log in button", ref=<ref_for_submit>)`
6. `mcp__playwright__browser_wait_for(time=2)` — wait for redirect to complete
7. `mcp__playwright__browser_snapshot()` — confirm you are no longer on the login page (URL changes or login form disappears)

**If login is not required:** Skip directly to Step 4.

**Headless note:** You cannot see the browser. Use `mcp__playwright__browser_snapshot()` after every significant navigation to confirm the page state before proceeding.

---

## Step 4: Navigate to the Feature URL

1. `mcp__playwright__browser_navigate(url="{url}")`
2. **For Blazor pages** (URI starts with `/Admin/`): `mcp__playwright__browser_wait_for(time=3)` — Blazor needs extra time to hydrate.
3. **For Razor Pages**: `mcp__playwright__browser_wait_for(time=1)` — standard wait.
4. `mcp__playwright__browser_snapshot()` — inspect the page state.

**What to look for in the snapshot:**
- Is the page content visible or is there still a loading indicator?
- Is there an empty state ("Basket is empty", "No results", etc.)?
- Is there data displayed (product tiles, order rows, etc.)?
- Are there any error messages or redirect indicators?

---

## Step 5: Determine Screenshot States

Based on the snapshot from Step 4, decide which states to capture:

**Single screenshot (most features):**
- Take one screenshot of the current page state.
- Name it `{key}.png`.

**Two screenshots (when a meaningful alternate state is easily reachable):**
- Capture the initial load state as `{key}.png`.
- If the functional spec describes an **empty state** (e.g., "Basket is empty." message) and the current snapshot already shows it — that IS the meaningful state. Name it `{key}-empty.png` instead.
- If the current state shows data (products listed, orders showing), also document that you would need seeded data to test the empty state — note it but don't attempt to clear data.

**What NOT to do:**
- Do not attempt to fill in forms or submit orders to manufacture a state.
- Do not try to add items to the basket or create orders.
- Capture the page as it loads naturally from the URL.

---

## Step 6: Capture Screenshots

For each screenshot:

1. `mcp__playwright__browser_take_screenshot(filename="screenshots/{name}.png")`
   - Playwright MCP saves to `.playwright-mcp/screenshots/{name}.png` in the cwd.
2. Move the file to `output_dir`:
   ```bash
   mkdir -p {output_dir}
   mv .playwright-mcp/screenshots/{name}.png {output_dir}/{name}.png
   ```
3. Confirm the move succeeded before taking the next screenshot.

**If the page is blank or shows a loading spinner only:**
- `mcp__playwright__browser_wait_for(time=3)` and retry the snapshot.
- If it's still blank after the extra wait, take the screenshot anyway and note the issue in the summary.

---

## Step 7: Create Completion Marker

After **all** screenshots have been successfully moved to `output_dir`, create the marker:

```bash
echo "$(date -Iseconds)" > {marker_path}
```

**IMPORTANT:** `marker_path` is a **file**, not a directory. Use the `>` redirect operator to write a timestamp string into it. Do NOT use `mkdir` here.

---

## Step 8: Close Browser

```
mcp__playwright__browser_close()
```

Do NOT use `pkill chrome` or any process-killing commands. The workflow manages process cleanup separately with PID isolation.

---

## Step 9: Report Summary

Output:
```
Feature key:     {key}
URL navigated:   {url}
Auth used:       {email used, or "none"}
Screenshots:     {list of filenames}
Output dir:      {output_dir}
Marker created:  {marker_path}
```

If any screenshot was blank or showed unexpected content, note it explicitly so the downstream `analyze-ui-feature` step knows to treat screenshot validation with caution.

---

## Worked Examples

### Example 1: Homepage catalog — no auth, single screenshot

**Input:**
```
key=homepage-catalog-list
url=http://localhost:5106/
output_dir=/abs/docs/entry-points/ui-features/homepage-catalog-list/screenshots
marker_path=/abs/.../screenshots/SCREENSHOTS_COMPLETE
```

1. No auth signals in metadata/spec — skip login.
2. Navigate to `http://localhost:5106/`.
3. Wait 1s. Snapshot shows: hero banner, brand/type filter selects, product tile grid (10 items).
4. One screenshot state: the loaded catalog page.
5. Take screenshot: `homepage-catalog-list.png`
6. Move to `output_dir`.
7. Create marker.
8. Close browser.

---

### Example 2: Basket page — anonymous user, empty state

**Input:**
```
key=basket-view-page
url=http://localhost:5106/Basket
output_dir=/abs/docs/entry-points/ui-features/basket-view-page/screenshots
marker_path=/abs/.../screenshots/SCREENSHOTS_COMPLETE
```

1. Metadata notes: "Anonymous users are tracked by a GUID stored in a cookie." Functional spec: auth not required for OnGet.
2. Skip login — anonymous access is allowed.
3. Navigate to `http://localhost:5106/Basket`.
4. Wait 1s. Snapshot shows: "Basket is empty." message + "Continue Shopping" link.
5. State is the empty basket — name screenshot `basket-view-page-empty.png`.
6. Take screenshot, move to `output_dir`.
7. Create marker. Close browser.

---

### Example 3: Admin catalog — requires admin login, Blazor page

**Input:**
```
key=admin-catalog-item-list
url=http://localhost:5106/Admin/Catalog
output_dir=/abs/docs/entry-points/ui-features/admin-catalog-item-list/screenshots
marker_path=/abs/.../screenshots/SCREENSHOTS_COMPLETE
```

1. URI starts with `/Admin/` → login as `admin@microsoft.com`.
2. Navigate to `http://localhost:5106/Identity/Account/Login`.
3. Snapshot, fill email (`admin@microsoft.com`), fill password (`Pass@word1`), click "Log in".
4. Wait 2s. Snapshot confirms redirect away from login page.
5. Navigate to `http://localhost:5106/Admin/Catalog`.
6. **Wait 3s** (Blazor page — extra hydration time).
7. Snapshot: catalog item list table visible with items.
8. Take screenshot: `admin-catalog-item-list.png`. Move to `output_dir`.
9. Create marker. Close browser.

---

### Example 4: No URL provided (app not running)

**Input:**
```
key=checkout-page
legacy_dir=/abs/path/source
file=src/Web/Pages/Basket/Checkout.cshtml
output_dir=/abs/docs/entry-points/ui-features/checkout-page/screenshots
marker_path=/abs/.../screenshots/SCREENSHOTS_COMPLETE
```

1. No `url` arg found — only `file`. App is not running.
2. Create the output directory and write the marker with a skip note.
3. Report: "Skipped — no `url` argument. Start eShopOnWeb (`dotnet run --project src/Web/Web.csproj`) and re-run."

---

## Important Notes

1. **Always snapshot before clicking.** Element refs change after every navigation and click. Stale refs cause silent failures.

2. **Headless = invisible browser.** Use `mcp__playwright__browser_snapshot()` liberally to understand page state. The accessibility tree snapshot is your only view into the browser.

3. **SCREENSHOTS_COMPLETE is a file, not a folder.** `echo "..." > {marker_path}` — never `mkdir {marker_path}`.

4. **Playwright saves to `.playwright-mcp/screenshots/`, not `output_dir`.** Always move files after taking a screenshot. If the move fails, the screenshot is lost.

5. **Blazor pages need 3s extra wait.** Any URI under `/Admin/` uses Blazor Server. Standard Razor Pages need 1s.

6. **Do not manufacture state.** Only capture what the page shows on natural load. Do not add items, create records, or navigate sub-flows to set up a specific state.

7. **One screenshot is fine.** Most features only need one screenshot. Two only when there's a clearly distinct empty vs loaded state that's immediately apparent on page load without interaction.

8. **Idempotency.** If `SCREENSHOTS_COMPLETE` already exists at `marker_path`, stop immediately without re-running. The workflow uses its presence as a gate.

9. **The eShopOnWeb app port.** The default port from `CLAUDE.md` is `5106` (Web) and `5200` (PublicApi). The `url` arg from the workflow will always contain the correct port — do not hardcode it.
