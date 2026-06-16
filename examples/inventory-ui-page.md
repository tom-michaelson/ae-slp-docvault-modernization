# Inventory UI Page (Simplified)

You are tasked with creating a simplified, factual inventory of UI pages from the Northwest Passage legacy application. This command extracts essential information about pages, panels, and actions into a flat JSON structure.

## User Query
{{PROMPT}}

## Command Syntax

### Usage
```
menu_id:<menu-item-id>
page_key:<key>
```

**Example:**
```
menu_id:2105
page_key: 2105-my-page
```

## Output

Each page gets its own folder under `./docs/entry-points/ui-pages/{page_key}/inventory.json` where `{page_key}` is the kebab-case menu path.

**Structure:** Array containing the page entry, followed by all panel entries, followed by all action entries.

**Type Structure:** All elements have `"type": "ui-feature"` with their specific type in `"elementType"`.

```json
[
  {
    "key": "infrastructure-company-trans-company-reports",
    "type": "ui-feature",
    "elementType": "ui-page-table-list",
    "domain": "company",
    "menuItemId": 967,
    "menuLabel": "Trans_Company_Reports",
    "menuPath": "Infrastructure > Company > Trans_Company_Reports",
    "uri": "modules/tables/views/table_list",
    "location": "./legacy/northwest-passage/passage-java/web/modules/tables/views/table_list.html",
    "tableName": "dbo.trans_company_reports",
    "mode": "P",
    "isGenericTablePage": true
  },
  {
    "key": "infrastructure-company-company-maintenance",
    "type": "ui-feature",
    "elementType": "ui-page",
    "domain": "company",
    "menuItemId": 2105,
    "menuLabel": "Company Maintenance",
    "menuPath": "Infrastructure > Company > Company Maintenance",
    "uri": "modules/company/companyMaint/views/company_maint",
    "location": "./legacy/northwest-passage/passage-java/web/modules/company/companyMaint/views/company_maint.html",
    "hasSearchBar": true,
    "hasAdvancedSearchBar": true
  },
  {
    "key": "infrastructure-company-company-maintenance-grid",
    "type": "ui-feature",
    "elementType": "ui-panel-data-table",
    "parentKey": "infrastructure-company-company-maintenance",
    "location": "./legacy/northwest-passage/passage-java/web/modules/company/companyMaint/views/company_maint.html:15",
    "hasSearchBar": false,
    "hasAdvancedSearchBar": false
  },
  {
    "key": "infrastructure-company-company-maintenance-details",
    "type": "ui-feature",
    "elementType": "ui-panel-form",
    "parentKey": "infrastructure-company-company-maintenance",
    "location": "./legacy/northwest-passage/passage-java/web/modules/company/companyMaint/views/company_maint.html:45"
  },
  {
    "key": "infrastructure-company-company-maintenance-address",
    "type": "ui-feature",
    "elementType": "ui-panel-data-table",
    "parentKey": "infrastructure-company-company-maintenance",
    "location": "./legacy/northwest-passage/passage-java/web/modules/company/companyMaint/views/company_maint.html:243",
    "hasSearchBar": false,
    "hasAdvancedSearchBar": false,
    "controllerName": "company.company_addressController"
  },
  {
    "key": "infrastructure-company-company-maintenance-grid-new",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-grid",
    "actionName": "New",
    "actionType": "modal-crud",
    "openedFrom": "moduleService.util.popupWindow($scope, \"modules/company/companyMaint/views/company_maint_new\", \" \",700,530)"
  }
]
```

## Exclusion Criteria

The following URI patterns are **excluded** from inventory processing:

### Flash Widgets (.swf files) - 14 occurrences across system
**Pattern**: URIs ending with `.swf` or equal to `url.swf`

**Reason**: Deprecated Flash technology - not modern AngularJS pages

**Examples**:
- `modules/widgets/generalWidgets/CycleStatusWidget.swf` (Dashboard widget)
- `modules/contractList/ContractPopupPod.swf` (Pod container)
- `modules/infrastructure/mobile/MobileInstallerPod.swf` (Mobile installer)
- `url.swf` (Servlet wrappers pointing to JSP pages or servlet commands)

**Categories of Flash widgets found**:
- Dashboard widgets (8 occurrences) - Under parent_id 1042
- Pod/Container widgets (2 occurrences) - Under parent_id 1798
- Mobile installer (1 occurrence)
- URL-based servlets (3 occurrences) - Flash containers for servlet content

### NULL/Empty URIs
**Pattern**: NULL or empty URI values

**Reason**: Menu structure items without associated pages (parent menu items, separators, etc.)

**Note on Generic Table Pages**: Pages with `uri = "modules/tables/views/table_list"` are NOT excluded - they are processed in Phase 0 with special handling as `ui-page-table-list` entries.

## Discovery Process

### Phase 0: Detect Generic Table-List Pages

**Data Source:** `./docs/foundational-analysis/ui-navigation/database-exports/menu-hierarchy.csv`

**Purpose:** Identify pages that use the generic metadata-driven table controller pattern. These pages share a single view file and controller, differing only in table name and display mode.

**Detection Logic:**
1. Read domain-menu-mapping.json to get menuParentId for domain
2. Filter menu-hierarchy.csv by parent_id matching menuParentId
3. Identify entries where `uri = "modules/tables/views/table_list"`
4. For each match, parse the `pod_params` column

**Parse pod_params:**
- Format: `tablename=<table_name>;mode=<mode>`
- Extract `tableName` (e.g., "dbo.trans_company_reports")
- Extract `mode` (e.g., "P", "V", or "H"; default to "H" if not specified)

**Create entry:**
```json
{
  "key": "infrastructure-company-trans-company-reports",
  "type": "ui-feature",
  "elementType": "ui-page-table-list",
  "domain": "company",
  "menuItemId": 967,
  "menuLabel": "Trans_Company_Reports",
  "menuPath": "Infrastructure > Company > Trans_Company_Reports",
  "uri": "modules/tables/views/table_list",
  "location": "./legacy/northwest-passage/passage-java/web/modules/tables/views/table_list.html",
  "tableName": "dbo.trans_company_reports",
  "mode": "P",
  "isGenericTablePage": true
}
```

**Field Descriptions:**
- `key`: kebab-case version of full menuPath (e.g., "Infrastructure > Company > Trans_Company_Reports" → "infrastructure-company-trans-company-reports")
- `type`: Always "ui-feature"
- `elementType`: Always "ui-page-table-list"
- `domain`: From user input
- `menuItemId`, `menuLabel`, `menuPath`: From menu-hierarchy.csv
- `uri`: Always "modules/tables/views/table_list"
- `location`: Always "./legacy/northwest-passage/passage-java/web/modules/tables/views/table_list.html"
- `tableName`: Extracted from pod_params
- `mode`: Extracted from pod_params (P=popup, V=vertical split, H=horizontal split)
- `isGenericTablePage`: Always true

**Note:** All generic table pages use the same controller (`tables.tableListController`) and service (`tables.tableService`), so these are not stored in the inventory.

**IMPORTANT:** Skip Phases 1-3 for these pages. The view file, controller, and service are shared across all 56+ generic table pages, so there's no need to analyze them repeatedly.

**Modernization Note:** These pages represent a significant opportunity - they can all be replaced with a single modern component that uses table metadata. This pattern affects 56+ menu items in the legacy system.

### Phase 1: Extract ui-page Entries

**Data Source:** `./docs/foundational-analysis/ui-navigation/database-exports/menu-hierarchy.csv`

**Steps:**
1. Read domain-menu-mapping.json to get menuParentId for domain
2. Filter menu-hierarchy.csv by parent_id matching menuParentId
3. **EXCLUDE entries where**:
   - `uri = "modules/tables/views/table_list"` (handled in Phase 0 as generic table pages)
   - `uri` ends with `.swf` (deprecated Flash widgets - see Exclusion Criteria)
   - `uri = "url.swf"` (deprecated servlet wrappers - see Exclusion Criteria)
   - `uri` is NULL or empty (menu structure items without pages)
4. For each remaining menu item with a uri, create ui-page entry:
   - key: kebab-case version of full menuPath (see Key Generation Algorithm below)
   - type: "ui-feature"
   - elementType: "ui-page"
   - domain: from user input
   - menuItemId: item_id from CSV
   - menuLabel: label from CSV
   - menuPath: Build from hierarchy (e.g., "Infrastructure > Company > Company Maintenance")
   - uri: uri from CSV
   - location: Construct path: `./legacy/northwest-passage/passage-java/web/{uri}.html`
   - hasSearchBar: boolean (check HTML for page-level `<div w-search-bar>` BEFORE any `<div w-module-panel>`)
   - hasAdvancedSearchBar: boolean (check HTML for page-level `<div w-advanced-search-bar>` BEFORE any `<div w-module-panel>`)

**Key Generation Algorithm:**
1. Take the full `menuPath` value (e.g., "Infrastructure > Company > Company Maintenance")
2. Split by " > " separator → ["Infrastructure", "Company", "Company Maintenance"]
3. Convert each segment to kebab-case → ["infrastructure", "company", "company-maintenance"]
4. Join with "-" → "infrastructure-company-company-maintenance"
5. This is the page key

**Examples:**
- "Infrastructure > Company > Company Maintenance" → "infrastructure-company-company-maintenance"
- "Maintenance Schedule > Maintenence Map" → "maintenance-schedule-maintenence-map"
- "Infrastructure > Maintenance Schedule > Schedule" → "infrastructure-maintenance-schedule-schedule"
- "Nominations" → "nominations" (single segment, no separators)

### Phase 2: Extract Panel Entries

**Data Source:** HTML view files

**Panel Types and Identification:**

#### ui-panel-data-table
Look for: `<div w-module-panel ... >` containing `<div class="w-grid" kendo-grid="..."`

Check for panel-level search bars INSIDE this specific `<div w-module-panel>` block:
- `<div w-search-bar ...>` appears as a child of this `w-module-panel` → set hasSearchBar: true
- `<div w-advanced-search-bar ...>` appears as a child of this `w-module-panel` → set hasAdvancedSearchBar: true
- If search bars appear BEFORE the `w-module-panel` (at page level), they belong to the page entry, NOT this panel
- Set both to false if no search bars are found inside this panel

Check for dedicated controller:
- Look for nearest parent `<div ng-controller="...">` directive
- If the panel is inside a nested controller (not the main page controller), extract the controller name

**Example HTML (Page-level search bars, no dedicated controller):**
```html
<div ng-controller="company.company_maintController as vm">
    <!-- PAGE-LEVEL search bars (BEFORE w-module-panel) -->
    <div w-search-bar on-click="vm.onRefresh()">...</div>
    <div w-advanced-search-bar>...</div>

    <!-- Panel with NO search bars (page-level ones above belong to ui-page entry) -->
    <div w-module-panel menu-items="vm.menuItems" module-vm="vm">
        <div class="w-grid" kendo-grid="vm.dgcompMaint"></div>
    </div>
</div>
```
**Result:** ui-page entry gets hasSearchBar: true, hasAdvancedSearchBar: true. Panel entry gets both false.

**Example HTML (Panel-level search bar):**
```html
<div ng-controller="scada.operatorLogTabController as vm">
    <!-- Panel with search bar INSIDE -->
    <div w-module-panel menu-items="vm.menuItems" module-vm="vm">
        <div w-search-bar on-click="vm.onRefresh()">...</div>
        <div class="w-grid" kendo-grid="vm.dgOperatorLogs"></div>
    </div>
</div>
```
**Result:** ui-page entry gets hasSearchBar: false, hasAdvancedSearchBar: false. Panel entry gets hasSearchBar: true, hasAdvancedSearchBar: false.

**Example HTML (with dedicated controller):**
```html
<div ng-controller="company.company_maintController as vm">
    <!-- Main controller panel - no controllerName field -->
    <div w-module-panel menu-items="vm.menuItems">...</div>

    <!-- Nested controller panel - include controllerName field -->
    <div ng-controller="company.company_addressController as vm">
        <div w-module-panel menu-items="vm.menuItems">
            <div class="w-grid" kendo-grid="vm.dgaddress"></div>
        </div>
    </div>
</div>
```

**Create entry:**
- key: `{page-key}-{panel-name}` (e.g., "infrastructure-company-company-maintenance-grid")
- type: "ui-feature"
- elementType: "ui-panel-data-table"
- parentKey: page key
- location: `{file-path}:{line-number}`
- hasSearchBar: boolean (check for w-search-bar)
- hasAdvancedSearchBar: boolean (check for w-advanced-search-bar)
- controllerName: (optional) string - only include if panel has its own dedicated ng-controller (e.g., "company.company_addressController")

#### ui-panel-form
Look for: `<div ng-form="...">` or form sections in tab strips

Check for dedicated controller:
- Look for nearest parent `<div ng-controller="...">` directive
- If the form is inside a nested controller (not the main page controller), extract the controller name

**Example HTML:**
```html
<div ng-controller="company.company_maintController as vm">
    <div kendo-tab-strip="vm.tabOptionsOne">
        <li>Details</li>
        <div ng-form="vm.companyDetailsForm">
            <input type="input" ng-model="vm.selectedCompany.commonName" ng-disabled="true">
        </div>
    </div>
</div>
```

**Create entry:**
- key: `{page-key}-{form-name}` (e.g., "company-maintenance-details")
- type: "ui-feature"
- elementType: "ui-panel-form"
- parentKey: page key
- location: `{file-path}:{line-number}`
- controllerName: (optional) string - only include if form has its own dedicated ng-controller

#### ui-panel-display
Look for: Display-only sections without forms or grids

Check for dedicated controller:
- Look for nearest parent `<div ng-controller="...">` directive
- If the display panel is inside a nested controller (not the main page controller), extract the controller name

**Example HTML (with dedicated controller):**
```html
<div ng-controller="company.company_maintController as vm">
    <!-- Main grid panel -->
    <div w-module-panel>...</div>

    <!-- Display panel with its own controller -->
    <div ng-controller="infrastructure.companyController as vm">
        <div w-module-panel>
            <span>{{vm.contactDetails.companyName}}</span>
            <span>{{vm.contactDetails.companyAddress}}</span>
        </div>
    </div>
</div>
```

**Create entry:**
- key: `{page-key}-{display-name}`
- type: "ui-feature"
- elementType: "ui-panel-display"
- parentKey: page key
- location: `{file-path}:{line-number}`
- controllerName: (optional) string - only include if display panel has its own dedicated ng-controller

### Phase 2a: Follow Dynamic Content References

After Phase 2 completes, scan the page HTML (and any files discovered in this phase) for dynamic content loading patterns. These patterns load panel content from external files or behind conditional gates that Phase 2's inline scan misses.

**Apply these 5 rules in sequence.** Each rule may discover new HTML files; when it does, apply Phase 2 panel detection (w-module-panel, ng-form, display sections) to those files and add discovered panels to the same inventory as the parent page.

**Recursion safeguards:**
- Track all visited file paths to prevent infinite loops
- Maximum recursion depth: 3 levels
- Always resolve relative paths from the web root: `./legacy/northwest-passage/passage-java/web/`

**Metadata:** For each panel discovered via Phase 2a, add the optional field:
```json
"loadedVia": "ng-include" | "contentUrls" | "k-content-urls" | "showDiv" | "scroll-view"
```

---

#### Rule A — Follow `ng-include` External Templates

**Trigger:** The HTML contains an `ng-include` directive referencing an external template file:

```html
<div ng-include src="'modules/path/to/template.html'"></div>
```

or the attribute-style form:

```html
<div ng-include="'modules/path/to/template.html'"></div>
```

**Action:**
1. Extract the `src` (or `ng-include`) attribute value — strip surrounding single and double quotes
2. Resolve to full legacy path: `./legacy/northwest-passage/passage-java/web/{extracted-path}`
3. Read the included file
4. Apply Phase 2 panel detection (w-module-panel, ng-form, display sections) to the included file
5. For each panel found, create an inventory entry with:
   - `parentKey`: the parent **page** key (not the included file)
   - `location`: the included file path and line number (e.g., `./legacy/.../voucherStatus.html:21`)
   - `controllerName`: extract from the nearest ancestor `ng-controller` within the included file
   - `loadedVia`: `"ng-include"`
6. If the included file itself contains `ng-include`, `k-content-urls`, or `ng-if="vm.showDiv"` patterns, recursively apply the appropriate rules (respect max depth)

**Example (Page 2127 — Voucher Processing):**

The main HTML `voucherProcessing.html` contains:
```html
<div ng-include src="'modules/finance/vouchers/views/voucherStatus.html'"></div>
<div ng-include src="'modules/finance/vouchers/views/voucherStatusBlueSkies.html'"></div>
```

→ Read `voucherStatus.html` → find 38 `w-module-panel` instances → create 38 panel entries
→ Read `voucherStatusBlueSkies.html` → find `ng-if="vm.showDiv"` blocks → apply Rule D recursively

**Example (Page 2122 — DOR):**

The main HTML `daily_operational_report.html` contains 6 ng-include directives:
```html
<div ng-include="'modules/scheduling/dailyOperationalReport/views/dailyOperationalReportMain.html'"></div>
<div ng-include="'modules/scheduling/dailyOperationalReport/views/dailyOperationalReportStorage.html'"></div>
<!-- ... 4 more -->
```

→ Read each file → apply Phase 2 panel detection → create panel entries for each

---

#### Rule B — Follow `vm.contentUrls` from Controller JS

**Trigger:** The page's controller JavaScript file contains a `vm.contentUrls` array assignment:

```javascript
vm.contentUrls = [
    { title: 'Tab Name', url: 'modules/path/to/tab.html' },
    // ... more entries
];
```

The HTML will typically have a corresponding `kendo-tab-strip` with `k-content-urls="vm.contentUrls"`:
```html
<div kendo-tab-strip="vm.tabStrip" k-content-urls="vm.contentUrls">
```

**Action:**
1. When the HTML contains `k-content-urls="vm.contentUrls"` (or `k-content-urls="vm.someVariable"`), identify the variable name
2. Find the page's controller JS file (mapped from the `ng-controller` directive wrapping the tab strip)
3. Open the controller file and locate the variable assignment (e.g., `vm.contentUrls = [...]`)
4. Extract all `url` property values from the array objects
5. For each URL: resolve to `./legacy/northwest-passage/passage-java/web/{url}`
6. Read each tab file and apply Phase 2 panel detection
7. Create panel entries with:
   - `parentKey`: the parent page key
   - `location`: the tab file path and line number
   - `loadedVia`: `"contentUrls"`

**Example (Page 901 — Contract List):**

HTML has: `k-content-urls="vm.contentUrls"`
Controller `create_offerController.js` (lines 86-103) has:
```javascript
vm.contentUrls = [
    { title: 'Locations', url: 'modules/contracts/.../locationsTab.html' },
    { title: 'Date Eff', url: 'modules/contracts/.../dateEffTab.html' },
    // ... 13 more entries
];
```

→ Read each of 15 tab HTML files → apply Phase 2 panel detection → create 15+ panel entries

**Example (Page 2141 — Morning Reports):**

Controller `morning_reportsController.js` (lines 57-66) has 8 tab URLs.

---

#### Rule C — Follow `k-content-urls` Hardcoded in HTML

**Trigger:** The HTML contains a `kendo-tab-strip` with `k-content-urls` set to a **hardcoded array literal** (not a variable reference):

```html
<div kendo-tab-strip k-content-urls="['modules/path/tab1.html', 'modules/path/tab2.html']">
```

**Key distinction from Rule B:** The URL array is embedded directly in the HTML attribute, not defined in a controller JS file. No JS file lookup is needed.

**Action:**
1. Parse the array literal from the `k-content-urls` attribute value
2. Extract all URL strings from the array
3. For each URL: resolve to `./legacy/northwest-passage/passage-java/web/{url}`
4. Read each tab file and apply Phase 2 panel detection
5. Create panel entries with `loadedVia: "k-content-urls"`
6. **Handle multiple tab strips per page independently** — a single page can have several `kendo-tab-strip` elements

**Example (Page 2154 — Invoice Processing):**

`invoiceProcessing.html` has 3 separate tab strips:

Strip 1 (line 5 — Maintenance): 9 tab URLs
```html
<div kendo-tab-strip k-content-urls="['modules/finance/invoices/views/associatedStdClauseMaint.html', ...]">
```

Strip 2 (line 22 — Pre-Processing): 5 tab URLs

Strip 3 (line 85 — Post-Processing): 8 tab URLs

→ Total: 22 tab files to read → apply Phase 2 panel detection to each → create 22+ panel entries

**Note:** If a tab file loaded via Rule C contains `ng-include` internally (e.g., `invoiceReconciliationNav.html`), apply Rule A recursively.

---

#### Rule D — Scan `ng-if="vm.showDiv == N"` Conditional Blocks

**Trigger:** The HTML (or an included file) contains conditional blocks using `vm.showDiv`:

```html
<div ng-if="vm.showDiv == 1">
    <div ng-controller="someController as vm">
        <div w-module-panel>...</div>
    </div>
</div>
<div ng-if="vm.showDiv == 2">
    <div ng-controller="anotherController as vm">
        <div w-module-panel>...</div>
    </div>
</div>
```

**Why Phase 2 misses these:** The inline scan may only process the first/default visible block or treat conditionally hidden blocks as inactive. Rule D explicitly processes ALL `ng-if="vm.showDiv == N"` blocks regardless of the value of N.

**Action:**
1. Find all `ng-if="vm.showDiv == N"` wrapper divs (for any integer N)
2. For each block:
   a. Check if it contains `w-module-panel`, `ng-form`, or display content
   b. If yes: create a panel inventory entry
   c. Extract `ng-controller` from inside the block as the panel's `controllerName`
   d. Use the block's location (file path + line number) as the panel `location`
   e. Set `loadedVia: "showDiv"`
3. If a showDiv block contains `ng-include`, apply Rule A recursively

**Example (Page 2123 — Revenue Forecast Config):**

`revConfigNav.html` has 14 `ng-if="vm.showDiv == N"` blocks (N = 1 to 14):
- Block 1: Group Details List
- Block 2: Group List
- Block 3: Category List
- ... through Block 14

→ Process all 14 blocks → create panel entries for each that contains a panel element

**Shared template note:** `revConfigNav.html` is used by both page 2123 (loaded as a tab) and page 2135 (as the primary view). When inventorying each page, the panels from this file appear in each page's inventory with that page's key as `parentKey`.

---

#### Rule E — kendo-mobile-scroll-view Inline Pages

**Trigger:** The HTML contains a `<kendo-mobile-scroll-view>` with `<div data-role="page">` children:

```html
<kendo-mobile-scroll-view k-value="vm.scrollView">
    <div data-role="page">
        <!-- Page 1 content with panels -->
    </div>
    <div data-role="page">
        <!-- Page 2 content with panels -->
    </div>
</kendo-mobile-scroll-view>
```

**Why Phase 2 may miss these:** The `data-role="page"` wrapper divs create logical sections that may not match Phase 2's panel detection heuristics (which look for `w-module-panel`, `ng-form`, etc. at the top level).

**Action:**
1. Find all `<div data-role="page">` elements inside `<kendo-mobile-scroll-view>`
2. For each page div: apply Phase 2 panel detection within that div's content
3. Create panel entries with `loadedVia: "scroll-view"` for any panels not already captured by Phase 2
4. Avoid duplicates — if a panel was already found in Phase 2's inline scan, do not create a second entry

**Example (Page 902 — Contract Request):**

`rqst_view.html` has 12 `data-role="page"` divs inside a scroll-view:
- Page 1: Exhibit A (General Tab) — inline content
- Page 2: Locations Tab (has `ng-controller="rqstList.rqstLocationController"`)
- ... through Page 12

→ Scan each page div → create panel entries for any panels not already captured

---

### Phase 3: Extract Menu Action Entries

**Data Source:** Controller JavaScript files (main AND nested controllers)

**Location Pattern:** `./legacy/northwest-passage/passage-java/web/{module}/controllers/*Controller.js`

**CRITICAL: Pages can have multiple controllers!**

**Multi-Controller Detection Algorithm:**

1. **Identify ALL Controllers in HTML:**
   ```html
   <!-- Main controller at root -->
   <div ng-controller="company.company_maintController as vm">
       <!-- Panel with actions in main controller -->
       <div w-module-panel menu-items="vm.menuItems">...</div>

       <!-- Nested controller for a tab -->
       <div ng-controller="company.company_addressController as vm">
           <!-- Panel with actions in nested controller -->
           <div w-module-panel menu-items="vm.menuItems">...</div>
       </div>

       <!-- Another nested controller -->
       <div ng-controller="company.company_attachmentController as vm">
           <!-- Panel with different menu items array name -->
           <div w-module-panel menu-items="vm.attachmentMenuItems">...</div>
       </div>
   </div>
   ```

2. **Map Each Panel to Its Controller (CRITICAL - Follow This Algorithm EXACTLY):**

   **Algorithm to Find the Owning Controller for a Panel:**

   Starting from the `<div w-module-panel>` element:

   a. **Search upward** through parent elements looking for `ng-controller` attributes

   b. **Stop at the FIRST `ng-controller` you encounter** - this is the owning controller

   c. Extract the controller name from the `ng-controller` attribute value
      - Example: `ng-controller="infrastructure.usrController as vm"` → controller name is `infrastructure.usrController`

   d. Note the `menu-items` attribute value on the panel (e.g., `vm.menuItems`, `vm.userMenuItems`)

   **Example Walkthrough:**
   ```html
   <div ng-controller="infrastructure.baRequestController as vm">        <!-- Line 1: Main controller -->
       <div w-module-panel menu-items="vm.baRequestMenuItems">         <!-- Line 2: Panel A -->
           <div class="w-grid"></div>
       </div>

       <div ng-controller="infrastructure.companyController as vm">     <!-- Line 5: Nested controller -->
           <div w-module-panel>                                         <!-- Line 6: Panel B -->
               <span>{{vm.companyName}}</span>
           </div>
       </div>

       <div ng-controller="infrastructure.usrController as vm">         <!-- Line 11: Another nested controller -->
           <div w-module-panel menu-items="vm.userMenuItems">          <!-- Line 12: Panel C -->
               <div class="w-grid"></div>
           </div>
       </div>
   </div>
   ```

   **Correct Mappings:**
   - Panel A (line 2): Search up → find `infrastructure.baRequestController` at line 1 → **Panel A belongs to baRequestController**
   - Panel B (line 6): Search up → find `infrastructure.companyController` at line 5 → **Panel B belongs to companyController**
   - Panel C (line 12): Search up → find `infrastructure.usrController` at line 11 → **Panel C belongs to usrController**

   **Common Mistake to Avoid:**
   - ❌ WRONG: Assigning Panel C to baRequestController because it's the outermost controller
   - ✓ CORRECT: Panel C belongs to usrController because that's the NEAREST parent ng-controller

   **Implementation Steps:**
   1. Create a data structure to track controller-panel relationships
   2. For each `w-module-panel` found, record its line number
   3. Search backwards from the panel's line to find the nearest `ng-controller`
   4. Record: `{panelLine: X, controllerName: "...", menuItemsAttr: "..."}`
   5. Use this mapping when extracting actions from controller files

3. **Build Controller-to-File Mapping:**
   ```
   company.company_maintController → company_maintController.js
   company.company_addressController → company_addressController.js
   company.company_attachmentController → company_attachmentController.js
   ```

4. **For EACH Controller File, Extract Actions:**

   **Find Menu Items Arrays:**
   ```javascript
   // In company_maintController.js
   vm.menuItems = [
       { text: "New" },
       { text: "Modify" }
   ];

   // In company_addressController.js
   vm.menuItems = [
       { text: "New" },
       { text: "Modify" },
       { text: "Delete" }
   ];

   // In company_attachmentController.js
   vm.attachmentMenuItems = [
       { text: "Attach Document" },
       { text: "View Attachment" },
       { text: "Remove Attachment" }
   ];
   ```

   **Find Handler Functions (in same controller file):**
   ```javascript
   vm.onNew = function () {
       moduleService.util.popupWindow($scope, "path/to/modal", "Title", 700, 530);
   };

   vm.onModify = function () {
       // similar pattern
   };

   vm.onDelete = function () {
       moduleService.confirm("Delete", "Are you sure?", function() {
           service.deleteItem(item);
       });
   };
   ```

5. **Classify Action Type:**
   - **modal-crud**: Opens popup with moduleService.util.popupWindow
   - **modal-confirm**: Uses moduleService.confirm dialog
   - **modal-other**: Opens another type of non-confirmation or CRUD modal popup or dialog
   - **export**: Contains export-related logic (Excel, CSV)
   - **print**: Jasper report generation
   - **table-filter**: Opens a filter criteria popup dialog (via gridService.filterGrid) that allows users to set column-based filter conditions on a data grid
   - **api-call**: Direct service call without modal
   - **navigation**: Router state changes
   - **other**: Another action you cannot match to one of the above categories; CAUTION: use this sparingly

6. **Extract openedFrom:**
   - For modal actions, extract the full `moduleService.util.popupWindow(...)` call
   - For other actions, extract the primary service/API call

**Create entry for EACH action in EACH controller:**
- key: `{page-key}-{panel-name}-{action-name}` (e.g., "company-maintenance-address-new")
- type: "ui-feature"
- elementType: "ui-menu-action"
- pageKey: page key
- panelKey: parent panel key (the panel that has the menu-items attribute in this controller's scope)
- actionName: text from menuItems array (e.g., "New", "Modify")
- actionType: classification (modal-crud, modal-confirm, modal-other, export, print, table-filter, api-call, navigation, other)
- openedFrom: full call statement or primary logic

**Example Results for Company Maintenance:**
- Main controller actions → company-maintenance-grid panel
- Address controller actions → company-maintenance-address panel
- Attachment controller actions → company-maintenance-attachments panel

## Search Bar Pattern Reference

Search bars in the Northwest Passage application exist at two distinct levels:

### Page-Level Search Bars (Most Common Pattern)
Page-level search bars appear BEFORE any `<div w-module-panel>` elements and filter data for the entire page.

**Location:** Typically inside `<div w-pod-panel>` at the root level
**Purpose:** Primary filter controls for retrieving page data
**Behavior:** User configures search criteria, clicks "Retrieve" button, then data loads into panel grids

**Structural Pattern:**
```html
<div w-pod-panel module-vm="vm">
    <div w-search-bar on-click="vm.onRefresh()" button-label="'Retrieve'">
        <!-- Date pickers, lookups, dropdowns, etc. -->
    </div>
    <div w-advanced-search-bar>
        <!-- Secondary/computed filter fields -->
    </div>
    <div w-module-panel>
        <!-- Panel content -->
    </div>
</div>
```

**Concrete Examples:**
1. **Daily Volumes** (`flowingGas/reports/dailyVolumes/views/daily_volumes.html`)
   - Line 3: `<div w-search-bar>` with Last Date Closed, Meter lookup
   - Line 15: `<div w-advanced-search-bar>` with Accounting Month, Year
   - Line 23: `<div w-module-panel>` with data grid
   - Result: Page gets both search bars, panel gets neither

2. **Company Maintenance** (`company/companyMaint/views/company_maint.html`)
   - Line 3-7: `<div w-search-bar>` with company lookup, name input
   - Line 8-13: `<div w-advanced-search-bar>` with active flag, effective date
   - Line 16: `<div w-module-panel>` with main grid
   - Result: Page gets both search bars, main panel gets neither

### Panel-Level Search Bars (Less Common, But Present)
Panel-level search bars appear INSIDE specific `<div w-module-panel>` elements and control only that panel's data.

**Location:** As children of `<div w-module-panel>`
**Purpose:** Panel-specific filter controls
**Common in:** Dashboard widgets, tabbed interfaces, finance/reporting screens with multiple independent panels

**Structural Pattern:**
```html
<div w-module-panel module-vm="vm">
    <div w-search-bar on-click="vm.onRefresh()">
        <!-- Panel-specific filters -->
    </div>
    <div class="w-grid" kendo-grid="vm.dgData"></div>
</div>
```

**Concrete Examples:**
1. **Operator Log Tab** (`scada/mrs/views/operatorLogTab.html`)
   - Line 3: `<div w-module-panel>` starts
   - Line 4: `<div w-search-bar>` INSIDE panel with Hours, Morning Report flag
   - Line 11: Data grid
   - Result: Page gets no search bars, panel gets hasSearchBar: true

2. **Nomination History Widget** (`infrastructure/dashboard/views/nominationHistory.html`)
   - Line 3: `<div w-module-panel>` starts (dashboard widget)
   - Line 7: `<div w-search-bar>` INSIDE panel with agency lookup, gas day
   - Line 13: Tree list grid
   - Result: Page gets no search bars, panel gets hasSearchBar: true

3. **SOX Review - IM Matrix Report** (`security/soxReview/views/ImMatrixReportTab.html`)
   - TWO panels, each with its own search bar
   - Line 20-26: First panel with search bar inside
   - Line 36-42: Second panel with search bar inside
   - Result: Page gets no search bars, each panel gets hasSearchBar: true

### Detection Algorithm Summary

**For ui-page entries:**
1. Scan HTML from start until first `<div w-module-panel>` appears
2. Look for `<div w-search-bar>` in this region → page-level
3. Look for `<div w-advanced-search-bar>` in this region → page-level
4. Set page entry's hasSearchBar and hasAdvancedSearchBar fields

**For ui-panel-data-table entries:**
1. Identify the specific `<div w-module-panel>` boundary
2. Look for `<div w-search-bar>` as a CHILD of this panel → panel-level
3. Look for `<div w-advanced-search-bar>` as a CHILD of this panel → panel-level
4. Set panel entry's hasSearchBar and hasAdvancedSearchBar fields
5. Ignore any page-level search bars that appear before this panel

**Key Principle:** Search bars belong to the NEAREST container:
- Before all panels = page-level
- Inside a panel = panel-level
- Never double-count (a search bar belongs to either page OR panel, not both)

## Implementation Workflow

### Step 1: Parse Parameters
Extract menuItemId from user query (e.g., `menu_id:2105`).

### Step 2: Load Reference Data
1. Read `./docs/foundational-analysis/ui-navigation/database-exports/menu-hierarchy.csv`
2. Find the row matching the menuItemId from Step 1
3. Extract domain, menuLabel, menuPath, uri, and pod_params (if applicable)
4. This single menu item is the page to process

### Step 3: Process the Page

For the menu item identified in Step 2:

1. **Create ui-page entry** from menu-hierarchy data

2. **Read HTML file** to identify panels AND controllers:

   **Step 2a: Find ALL ng-controller directives**
   - Scan the entire HTML file for ALL `ng-controller` attributes
   - Record: controller name, line number, and nesting level
   - Example findings:
     ```
     Line 1: infrastructure.baRequestController (main)
     Line 17: infrastructure.companyController (nested in main)
     Line 79: infrastructure.usrController (nested in main)
     ```

   **Step 2b: Find ALL panels (w-module-panel)**
   - Scan for all `<div w-module-panel>` elements
   - For EACH panel found, record its line number
   - Example findings:
     ```
     Line 12: w-module-panel with menu-items="vm.baRequestMenuItems"
     Line 19: w-module-panel (no menu-items attribute)
     Line 81: w-module-panel with menu-items="vm.userMenuItems"
     ```

   **Step 2c: Map each panel to its owning controller**
   - For EACH panel:
     1. Starting from the panel's line number
     2. Search BACKWARDS through the HTML
     3. Find the FIRST `ng-controller` attribute you encounter
     4. That controller OWNS this panel
   - Example mappings:
     ```
     Panel at line 12 → search back → find controller at line 1 → baRequestController
     Panel at line 19 → search back → find controller at line 17 → companyController
     Panel at line 81 → search back → find controller at line 79 → usrController
     ```

   **Step 2d: Determine panel characteristics**
   - For each panel:
     - Determine panel type:
       - w-module-panel + kendo-grid → data-table panel
       - ng-form → form panel
       - Other → display panel
     - Check for w-search-bar and w-advanced-search-bar (look BEFORE the panel, not inside nested controllers)
     - Record the menu-items attribute value if present
     - Record the owning controller name (from Step 2c)
   - Create panel entry with:
     ```json
     {
       "panelLine": 81,
       "panelType": "ui-panel-data-table",
       "controllerName": "infrastructure.usrController",
       "menuItemsAttr": "vm.userMenuItems",
       "hasSearchBar": false,
       "hasAdvancedSearchBar": false
     }
     ```

3. **Read ALL Controller files** to identify actions:

   **Step 3a: Get unique list of controllers**
   - From Step 2a, extract the unique set of controller names
   - Example: `["infrastructure.baRequestController", "infrastructure.companyController", "infrastructure.usrController"]`

   **Step 3b: For EACH controller, find and read its file**
   - Map controller name to file path:
     - `infrastructure.baRequestController` → `ba_requestController.js`
     - `infrastructure.companyController` → `company_Controller.js`
     - `infrastructure.usrController` → `user_Controller.js`
   - Read the controller file

   **Step 3c: For EACH controller file, extract menu items and actions**
   - Find menu items array(s) in the controller:
     ```javascript
     vm.baRequestMenuItems = [
         { text: "Edit BA Request" },
         { text: "Print" }
     ];
     ```
   - Find corresponding handler functions (vm.onEditBARequest, vm.onPrint, etc.)
   - Classify each action type based on implementation

   **Step 3d: Match actions to the correct panel**
   - Use the panel-controller mapping from Step 2c
   - For each action found in a controller:
     1. Look up which panel(s) belong to this controller
     2. Check if the panel has a menu-items attribute that matches the array name
     3. Link the action to that specific panel
   - Example:
     ```
     Action: "Print" from usrController (array: vm.userMenuItems)
     → Find panel owned by usrController with menu-items="vm.userMenuItems"
     → Panel at line 81 (ba-request-users-grid)
     → Create action entry with panelKey="ba-request-users-grid"
     ```

   **CRITICAL: One controller can have multiple panels, and actions only apply to panels with matching menu-items attributes**

4. **Link everything:**
   - Panels link to page via parentKey (use the FULL key)
   - Actions link to page via pageKey (use the FULL key)
   - Actions link to panel via panelKey (use the FULL key)

### Step 4: Write Output

1. Create folder: `./docs/entry-points/ui-pages/{page-key}/`
2. Write all entries (page, panels, actions) to `./docs/entry-points/ui-pages/{page-key}/inventory.json` as a flat array
3. Overwrite the file if it exists (each run generates complete inventory for that page)
4. **Validate the output** using the validation tool:
   ```bash
   node .claude/tools/validate-ui-inventory.js ./docs/entry-points/ui-pages/{page-key}/inventory.json
   ```
5. Fix any validation errors before proceeding

### Step 5: Report Summary

Display:
- Page processed: {menuItemId} - {menuLabel}
- Page type: {elementType}
- Output location: ./docs/entry-points/ui-pages/{page-key}/inventory.json
- Panels found: Z
  - Data tables: D
  - Forms: E
  - Displays: F
- Actions found: G
  - modal-crud: H
  - modal-confirm: I
  - modal-other: I
  - export: J
  - print: K
  - table-filter: L
  - api-call: M
  - navigation: N
  - other: O

## Examples

### Example 1: Process Company Maintenance Page
```
/inventory-ui-page menu_id:2105
```

Processes the Company Maintenance page (menuItemId 2105) and outputs to:
- `./docs/entry-points/ui-pages/infrastructure-company-company-maintenance/inventory.json`

### Example 2: Process a Generic Table Page
```
/inventory-ui-page menu_id:967
```

Processes the Trans_Company_Reports page (menuItemId 967) and outputs to:
- `./docs/entry-points/ui-pages/infrastructure-company-trans-company-reports/inventory.json`

### Example 3: Expected Output for Company Maintenance (Multi-Controller Page)

This page has 3 controllers:
- company_maintController (main)
- company_addressController (nested)
- company_attachmentController (nested)

Output location: `./docs/entry-points/ui-pages/infrastructure-company-company-maintenance/inventory.json`

Expected inventory entries:

```json
[
  {
    "key": "infrastructure-company-company-maintenance",
    "type": "ui-feature",
    "elementType": "ui-page",
    "...": "..."
  },
  {
    "key": "infrastructure-company-company-maintenance-grid",
    "type": "ui-feature",
    "elementType": "ui-panel-data-table",
    "parentKey": "infrastructure-company-company-maintenance",
    "hasSearchBar": true,
    "hasAdvancedSearchBar": true
  },
  {
    "key": "infrastructure-company-company-maintenance-address",
    "type": "ui-feature",
    "elementType": "ui-panel-data-table",
    "parentKey": "infrastructure-company-company-maintenance",
    "hasSearchBar": false,
    "hasAdvancedSearchBar": false,
    "controllerName": "company.company_addressController"
  },
  {
    "key": "infrastructure-company-company-maintenance-attachments",
    "type": "ui-feature",
    "elementType": "ui-panel-data-table",
    "parentKey": "infrastructure-company-company-maintenance",
    "hasSearchBar": false,
    "hasAdvancedSearchBar": false,
    "controllerName": "company.company_attachmentController"
  },
  {
    "key": "infrastructure-company-company-maintenance-grid-new",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-grid",
    "actionName": "New",
    "actionType": "modal-crud",
    "openedFrom": "moduleService.util.popupWindow(...company_maint_new...)"
  },
  {
    "key": "infrastructure-company-company-maintenance-grid-modify",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-grid",
    "actionName": "Modify",
    "actionType": "modal-crud",
    "openedFrom": "moduleService.util.popupWindow(...company_maint_modify...)"
  },
  {
    "key": "infrastructure-company-company-maintenance-address-new",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-address",
    "actionName": "New",
    "actionType": "modal-crud",
    "openedFrom": "FROM company_addressController.js"
  },
  {
    "key": "infrastructure-company-company-maintenance-address-modify",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-address",
    "actionName": "Modify",
    "actionType": "modal-crud",
    "openedFrom": "FROM company_addressController.js"
  },
  {
    "key": "infrastructure-company-company-maintenance-attachments-attach",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-attachments",
    "actionName": "Attach Document",
    "actionType": "modal-crud",
    "openedFrom": "FROM company_attachmentController.js"
  },
  {
    "key": "infrastructure-company-company-maintenance-attachments-view",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-attachments",
    "actionName": "View Attachment",
    "actionType": "modal-crud",
    "openedFrom": "FROM company_attachmentController.js"
  },
  {
    "key": "infrastructure-company-company-maintenance-attachments-remove",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-company-maintenance",
    "panelKey": "infrastructure-company-company-maintenance-attachments",
    "actionName": "Remove Attachment",
    "actionType": "modal-confirm",
    "openedFrom": "FROM company_attachmentController.js"
  }
]
```

**Note:** This shows ~8 actions total across 3 data-table panels from 3 different controllers.

### Example 4: Expected Output for BA Request (Multi-Controller with Display Panel)

This page has 3 controllers managing different panels:
- infrastructure.baRequestController (main) - manages request grid
- infrastructure.companyController (nested) - manages display-only company info
- infrastructure.usrController (nested) - manages users grid

Output location: `./docs/entry-points/ui-pages/infrastructure-company-ba-request/inventory.json`

Expected inventory entries showing CORRECT controller-to-panel mapping:

```json
[
  {
    "key": "infrastructure-company-ba-request",
    "type": "ui-feature",
    "elementType": "ui-page",
    "...": "..."
  },
  {
    "key": "infrastructure-company-ba-request-grid",
    "type": "ui-feature",
    "elementType": "ui-panel-data-table",
    "parentKey": "infrastructure-company-ba-request",
    "location": "...html:12",
    "hasSearchBar": true,
    "hasAdvancedSearchBar": true
  },
  {
    "key": "infrastructure-company-ba-request-company-display",
    "type": "ui-feature",
    "elementType": "ui-panel-display",
    "parentKey": "infrastructure-company-ba-request",
    "location": "...html:19",
    "controllerName": "infrastructure.companyController"
  },
  {
    "key": "infrastructure-company-ba-request-users-grid",
    "type": "ui-feature",
    "elementType": "ui-panel-data-table",
    "parentKey": "infrastructure-company-ba-request",
    "location": "...html:81",
    "hasSearchBar": false,
    "hasAdvancedSearchBar": false,
    "controllerName": "infrastructure.usrController"
  },
  {
    "key": "infrastructure-company-ba-request-grid-edit-ba-request",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-ba-request",
    "panelKey": "infrastructure-company-ba-request-grid",
    "actionName": "Edit BA Request",
    "actionType": "modal-crud",
    "openedFrom": "FROM baRequestController (vm.baRequestMenuItems)"
  },
  {
    "key": "infrastructure-company-ba-request-users-grid-print",
    "type": "ui-feature",
    "elementType": "ui-menu-action",
    "pageKey": "infrastructure-company-ba-request",
    "panelKey": "infrastructure-company-ba-request-users-grid",
    "actionName": "Print",
    "actionType": "print",
    "openedFrom": "FROM usrController (vm.userMenuItems)"
  }
]
```

**Key Observations:**
- ✅ infrastructure-company-ba-request-grid has NO controllerName (it belongs to main controller)
- ✅ infrastructure-company-ba-request-company-display has controllerName="infrastructure.companyController" (nested, no actions)
- ✅ infrastructure-company-ba-request-users-grid has controllerName="infrastructure.usrController" (nested, has actions)
- ✅ Actions from baRequestController link to infrastructure-company-ba-request-grid (NOT to users-grid)
- ✅ Actions from usrController link to infrastructure-company-ba-request-users-grid (NOT to request-grid)

**Common Mistakes to Avoid:**
- ❌ Assigning infrastructure-company-ba-request-users-grid to baRequestController (it's owned by usrController at line 79)
- ❌ Linking usrController actions to infrastructure-company-ba-request-grid (they belong to different controllers)
- ❌ Adding controllerName to infrastructure-company-ba-request-grid (it's managed by main controller)

### Example 5: Generic Table-List Pages (Phase 0)

**Scenario:** Processing Trans_Company_Reports (menuItemId: 967)

**Input:** `menu-hierarchy.csv` contains:
```
item_id,label,parent_id,uri,pod_params
967,Trans_Company_Reports,964,modules/tables/views/table_list,tablename=dbo.trans_company_reports;mode=P
```

Output location: `./docs/entry-points/ui-pages/infrastructure-company-trans-company-reports/inventory.json`

**Phase 0 Output:**
```json
[
  {
    "key": "infrastructure-company-trans-company-reports",
    "type": "ui-feature",
    "elementType": "ui-page-table-list",
    "domain": "company",
    "menuItemId": 967,
    "menuLabel": "Trans_Company_Reports",
    "menuPath": "Infrastructure > Company > Trans_Company_Reports",
    "uri": "modules/tables/views/table_list",
    "location": "./legacy/northwest-passage/passage-java/web/modules/tables/views/table_list.html",
    "tableName": "dbo.trans_company_reports",
    "mode": "P",
    "isGenericTablePage": true
  }
]
```

**Key Observations:**
- ✅ Detected by `uri = "modules/tables/views/table_list"` in Phase 0
- ✅ `pod_params` parsed to extract table name and mode
- ✅ No panels or actions extracted (shared controller handles all 56+ generic pages)
- ✅ Controller and service names not stored (always `tables.tableListController` and `tables.tableService`)
- ✅ Phases 1-3 skipped for this page
- ✅ Lean inventory entry - only essential metadata stored

**Modernization Impact:**
This pattern appears 56+ times across the system. All instances can be replaced with a single modern component that reads table metadata, representing significant consolidation opportunity.

## Important Notes

1. **Factual Only:** This is a simple inventory. Do NOT add complexity scoring, analysis, or notes.
2. **Flat Structure:** All entries in one array, linked by keys (including numeric prefixes in all key references).
3. **Essential Fields Only:** Only capture the fields specified above.
4. **Line Numbers:** Always include line numbers in location fields for panels and actions.
5. **No README:** Only write to inventory.json, never create README files.
6. **Multi-Controller Pages:** ALWAYS process ALL controllers found in the HTML (main + nested). Each controller may have its own menu actions that must be cataloged.
7. **Verbose Key Naming:** All keys use the full menuPath converted to kebab-case.
   - Page: "Infrastructure > Company > Company Maintenance" → "infrastructure-company-company-maintenance"
   - Panel: "infrastructure-company-company-maintenance-grid"
   - Action: "infrastructure-company-company-maintenance-grid-new"
8. **Action Key Naming:** Use format `{page-key}-{panel-suffix}-{action-name-kebab}`
   - Example: "infrastructure-company-company-maintenance-grid-new" (from main controller)
   - Example: "infrastructure-company-company-maintenance-address-modify" (from nested controller)
   - Example: "infrastructure-company-company-maintenance-attachments-view" (from nested controller)
9. **Controller-to-File Mapping:** Extract controller name from ng-controller attribute (e.g., "company.company_addressController") and map to file (e.g., "company_addressController.js"). All files are in the same controllers directory.
10. **CRITICAL - Controller-to-Panel Mapping:** Each panel belongs to EXACTLY ONE controller - the NEAREST parent ng-controller found by searching BACKWARDS from the panel's location in the HTML. DO NOT assign a panel to an outer/ancestor controller if there is a nested controller between them. Example: If Panel X is at line 81 and there's a nested controller at line 79, Panel X belongs to the controller at line 79, NOT to the main controller at line 1.
11. **Action-to-Panel Linking:** Actions from a controller ONLY apply to panels that: (a) belong to that controller (nearest parent), AND (b) have a matching menu-items attribute. Do not assume all actions from a controller apply to all panels on the page.
12. **controllerName Field:** Only include the `controllerName` field on panels that have their own dedicated ng-controller (nested controllers). Panels managed by the main page controller should NOT have this field. This field helps identify panels with isolated, complex functionality that will need special attention during modernization.
13. **Generic Table-List Pages (Phase 0):** Pages with `uri = "modules/tables/views/table_list"` are handled in Phase 0 and receive the type `ui-page-table-list`. These pages are metadata-driven and share a single controller/service. DO NOT process these pages in Phases 1-3. This pattern affects 56+ pages across the system and represents a major modernization opportunity to build one reusable component instead of 56 custom pages.

## Quality Checks

**REQUIRED**: Validate output before completing:

```bash
node .claude/tools/validate-ui-inventory.js ./docs/entry-points/ui-pages/{page-key}/inventory.json
```

The validation tool checks:
- **Required fields**: `key`, `type`, `elementType` must be present
- **Key format**: Must be lowercase kebab-case (e.g., "infrastructure-company-company-maintenance")
- **No duplicates**: Each key must be unique within the file
- **Valid enum values**: `elementType` and `actionType` must use valid values
- **Proper null values**: Use `null` not empty strings for optional fields
- **Parent-child references**: `parentKey`, `pageKey`, `panelKey` should reference existing keys
- **Type-specific requirements**: Actions need actionName/actionType, panels need parentKey, etc.

Fix all validation errors before proceeding. Warnings indicate potential issues that should be reviewed but don't block completion.

## Key Differences from Full Inventory

- ❌ No domain folders or page-specific JSON files
- ❌ No complexity assessment
- ❌ No detailed modal form field extraction
- ❌ No pattern analysis beyond action type classification
- ❌ No notes or descriptions
- ✅ Single flat inventory.json file
- ✅ Essential fields only
- ✅ Parent-child linking via keys
- ✅ Simple, factual extraction
