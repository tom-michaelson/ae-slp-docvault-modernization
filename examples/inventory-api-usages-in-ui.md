---
description: Inventory all UI-side invocations of a specific API endpoint and write results to ./docs/entry-points/api-endpoints/<key>/usages/ui.json
argument-hint: "key: [key] location: [location]"
---

# Inventory API Usages in UI

You are an expert codebase investigator tasked with locating every UI-side invocation of a single API endpoint.

**IMPORTANT**: You will receive two inputs:
1. **key** - A unique slug-style identifier for this endpoint (e.g., "01-my-endpoint")
2. **location** - The location in code of the entry point for this API endpoint

Proceed with whatever information is provided.

## Objective
Identify all places in the UI/front-end code where the target endpoint is actually called. Confirm that each reported call resolves to the exact endpoint (path segments, parameters, and HTTP method when known). Ignore comments, unused constants, or server-side-only code.

## High-Level Approach
1. **Interpret the endpoint definition**
   - Normalize the provided path (remove protocol/domains, align trailing slashes, recognise templated parameters such as `:id`, `{id}`, `<id>`, etc.).
   - Derive plausible runtime variants (with/without leading slash, version prefixes, query strings, case differences).
   - Note base URLs, API namespaces, or environment variables that might combine with the path.

2. **Map the UI code surface area**
   - Locate directories likely to contain front-end code (e.g. `src`, `app`, `packages/*`, `web`, `ui`, `client`, `frontend`, native mobile folders).
   - Include languages/frameworks such as TypeScript, JavaScript, JSX/TSX, Vue, Angular, Svelte, Elm, SwiftUI, Kotlin/Compose, Flutter/Dart, React Native, etc.
   - Exclude generated output (`dist`, `build`, `node_modules`, compiled artifacts) unless no other source exists.

3. **Search for direct path usage**
   - Scan UI files for string literals or template strings that match the endpoint path variants.
   - Capture surrounding context to see whether the string participates in a network call.

4. **Resolve dynamically constructed URLs**
   - Trace constants, configuration files, helper functions, and environment variables that define API hosts or path segments.
   - Follow imports/exports to where those pieces are composed into final URLs (string concatenation, template literals, array joins, URL builder utilities, router helpers, etc.).
   - Examine HTTP client calls (`fetch`, `axios`, `XMLHttpRequest`, `GraphQLClient`, `apollo`, `relay`, `trpc`, `rtk-query`, `urql`, `swr`, `ky`, native mobile networking, etc.) and evaluate argument values.
   - Confirm that substitutions (e.g., `/${userId}`) align with the endpoint pattern and would generate the target path at runtime.

5. **Trace reusable API abstractions**
   - Inspect service/data-access layers or generated clients that wrap HTTP calls (e.g., `ApiClient.get(endpointPath)`).
   - Follow call chains from UI components/screens/view-models into these helpers to verify the target endpoint is reached in real UI execution paths (respecting feature flags, platform conditions, or environment checks).

6. **Filter non-UI or irrelevant references**
   - Ignore server-only handlers unless they are imported into the UI bundle.
   - Exclude test fixtures, mocks, or Storybook examples unless they perform real network calls in production.

7. **Identify the innermost HTTP call layer**
   - **CRITICAL**: In layered architectures where controllers/components call services, and services make HTTP calls, record ONLY the innermost layer that directly invokes the HTTP client.
   - Common pattern to recognize:
     - **Service layer**: Functions that wrap `remoteService.post()`, `fetch()`, `axios()`, etc. and make the actual HTTP call → **RECORD THESE**
     - **Controller/Component layer**: Code that calls service layer functions → **DO NOT RECORD THESE**
   - How to distinguish:
     - Look for direct HTTP client invocations (`remoteService.post`, `fetch`, `axios.get`, `$http`, etc.)
     - If a file calls a service function (e.g., `agencyService.updateAgent(...)`), trace to the service definition
     - Record only where the HTTP client is actually invoked, not where the service wrapper is called
   - Example:
     ```javascript
     // Service file (agency_delegationService.js) - RECORD THIS
     var updateAgentDelegation = function(newParam, oldParam, callback){
         var postData = {...};
         return remoteService.post(endpoint, postData, null, callback); // ← Actual HTTP call
     };

     // Controller file (agency_delegation_modifyController.js) - DO NOT RECORD
     agencyDelegationService.updateAgentDelegation(vm.item, vm.selectedItem, function(data){
         // ← Just calling the service, not making HTTP call
     });
     ```
   - When you find multiple call sites in a chain, trace backwards to find where the HTTP call originates and record only that location.

8. **Record verified call sites**
   - For every confirmed UI invocation at the **innermost HTTP call layer**, capture the file path relative to the repository root, 1-based line number, and the nearest class/component/screen name when applicable (or `null` when not inside a class).
   - Deduplicate duplicate references pointing to the same call site.

## Output Location
**CRITICAL**: Write the output JSON to:
```
./docs/entry-points/api-endpoints/<name>/usages/ui.json
```

Where `<name>` is the slug-style identifier provided as input.

Create the directory structure if it doesn't exist.

## Output Format
The file must contain **only** a JSON array. Each element must be an object with this shape:
```json
[
  {
    "file": "relative/path/to/file.ext",
    "class": "ComponentOrScreenName | null",
    "line": 123
  }
]
```
- `file`: repository-relative path to the UI source file containing the network invocation.
- `class`: surrounding class/component/screen name, or `null` if not applicable.
- `line`: 1-based line number where the invocation occurs.

If no invocations exist, write `[]` to the file.

## Quality Checks
- Verify that each reported call truly resolves to the target endpoint path and (when provided) matches the HTTP method.
- Ensure JSON is valid and entries are unique.
- Repeat focused searches if wrappers or dynamic builders suggest additional call sites.
- Write only the JSON array to the output file—no narrative explanation or markdown formatting.
