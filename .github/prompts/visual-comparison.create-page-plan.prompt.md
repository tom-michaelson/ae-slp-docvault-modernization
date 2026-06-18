# Create Page Capture Plan

Reads a page's inventory and the metadata of every UI feature it owns, then
produces `page-capture-plan.json` listing every screenshot to capture. Both
sides (legacy + new) share this plan so filenames pair cleanly.

## Arguments

- `$ARGUMENTS` — the page key (folder name under `docs/entry-points/ui-pages/`).
  Examples: `home`, `document-list`.

## What This Does

1. Reads the page's inventory and the functional specs of its feature(s).
2. Identifies the **legacy URI** and **modern URI** for the page.
3. Produces a structured `page-capture-plan.json` listing every screenshot.
4. Validates the output.

## Step 1: Read Page and Feature Documentation

Read these (skip any that don't exist):

- `docs/entry-points/ui-pages/$ARGUMENTS/inventory.json` — the page's UI element inventory. The first entry with `elementType: "ui-page"` is the **top-level page entry**. Note its `key`, `uri`, and `domain`.
- `docs/entry-points/ui-pages/$ARGUMENTS/page-plan.json` *(optional)* — feature batches and dependency order.
- For the top-level page entry's `key` AND every other entry whose `key` matches a folder under `docs/entry-points/ui-features/`, read:
  - `docs/entry-points/ui-features/{key}/metadata.json` — note `uri` (modern), `legacyUri`, `domain`.
  - `docs/entry-points/ui-features/{key}/functional-spec.md` — note in-scope user actions and any flow scenarios in the Acceptance Criteria.

The top-level inventory entry usually carries the legacy URI in its `uri` field.
The matching ui-feature `metadata.json` carries the modern Angular URI in its
`uri` field and (often) the legacy URI in `legacyUri`. **Use the metadata.json
values as the source of truth when both are present**, falling back to the
inventory's `uri` for legacy if needed.

## Step 2: Pick the Page URIs

You need both:
- `legacyPath` — relative path on `localhost:3000` (e.g. `/documents`, `/`)
- `newPath` — relative path on `localhost:4200` (e.g. `/documents`, `/`)

These come from the metadata.json of the top-level ui-feature for the page. If
metadata.json only has `uri` and the page is at the same path on both sides
(e.g. `/`), use `uri` for both.

## Step 3: Identify Baseline Screenshots

Baseline screenshots capture static UI states. For every page:

1. **`main-view`** — always include this. The page after initial load (data
   fetched if applicable, no user interaction beyond navigation).

For each child UI element in the page's inventory.json, add a baseline only
when it is a distinct visible state worth its own screenshot:

2. **Tabs** — for each entry with `elementType: "ui-tab"`, add `{tab-slug}-tab`.
3. **Standalone panels** — for `elementType: "ui-panel"` entries that are NOT
   sub-components of another panel (i.e. their `parentKey` is the page itself),
   add `{panel-slug}-panel`. Skip panels that are just structural wrappers
   (table headers, item rows) — those show up inside `main-view`.
4. **Empty/loaded states** — if the page's functional spec describes a distinct
   empty-state branch (e.g. "Basket is empty"), add `empty-state` so the
   comparison can verify that branch separately.

Slugs are lowercase-hyphenated.

## Step 4: Identify Flow Screenshots

Flow screenshots capture interactive states (modals, post-action results, form
submissions). Read every feature's functional spec and find the flows
explicitly described in the **Acceptance Criteria** Gherkin scenarios. Convert
each interactive scenario to a flow screenshot:

- **Form-submission flows**: `flow-{action-slug}` (e.g. `flow-upload`,
  `flow-delete-document`)
- **Result states**: `flow-{action-slug}-result` for the post-submit view
- **Validation/error states**: `flow-{action-slug}-error`
- **Filter/search flows**: `flow-search`, `flow-filter-{name}`

Include ONLY flows that are described in a functional spec for a feature on
THIS page. Do not invent flows.

## Step 5: Write page-capture-plan.json

```bash
mkdir -p docs/entry-points/ui-pages/$ARGUMENTS/visual-comparison/
```

Write to `docs/entry-points/ui-pages/$ARGUMENTS/visual-comparison/page-capture-plan.json`:

```json
{
  "pageKey": "$ARGUMENTS",
  "pageSummary": "1-2 sentence description of what this page does.",
  "legacyPath": "/documents",
  "newPath": "/documents",
  "screenshots": [
    {
      "name": "main-view",
      "category": "baseline",
      "description": "Page after initial load with the typical populated state.",
      "navigationHint": "Navigate to the page URL; ensure any seeded data is present.",
      "expectedElements": ["primary content area", "key actions"]
    },
    {
      "name": "empty-state",
      "category": "baseline",
      "description": "Page rendered when the user has no documents yet.",
      "navigationHint": "Use a fresh anonymous session (clear cookies/localStorage) and navigate.",
      "expectedElements": ["empty-state copy", "primary call to action"]
    },
    {
      "name": "flow-upload",
      "category": "flow",
      "description": "After the user submits the upload form (post-submit state).",
      "navigationHint": "Fill in the upload form and click [ UPLOAD DOCUMENT ].",
      "expectedElements": ["success confirmation", "uploaded document in list"]
    }
  ]
}
```

**Rules:**
- `name`: filename stem only, no `.png`, lowercase hyphenated.
- `category`: `"baseline"` or `"flow"`.
- `legacyPath` and `newPath` are required, as plain relative paths starting
  with `/`.
- Order: all baselines first, then flows.

## Step 6: Validate

After writing, re-read and verify:
1. JSON parses cleanly.
2. `pageKey`, `pageSummary`, `legacyPath`, `newPath`, `screenshots` are all present.
3. Every screenshot has `name`, `category`, `description`.
4. `main-view` is the first baseline.
5. No duplicate `name` values.
6. All categories are `"baseline"` or `"flow"`.

## Success Criteria

- [ ] Page inventory + every page-feature's metadata + functional spec read
- [ ] `legacyPath` and `newPath` resolved
- [ ] Baselines list includes `main-view` and any distinct UI states (tabs/panels/empty)
- [ ] Flows list reflects only the Acceptance Criteria scenarios from feature specs
- [ ] `page-capture-plan.json` written and validated
