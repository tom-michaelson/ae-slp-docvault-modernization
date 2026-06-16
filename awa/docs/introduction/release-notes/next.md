# Latest Release Notes - ?

**Keep up with AWA's latest product news!**

Read the full documentation (links below) for more details on each feature.

Catch up on our full release notes archive [here](/introduction/release-notes/archive).

## UI Enhancements

### Nullable Workflow Input Support

The Web UI now provides improved handling for workflows with optional/nullable input parameters.

**Key Features:**

- **Checkbox Control**: When a workflow has nullable input, a "Override Defaults" checkbox appears below the workflow selector
- **Optional Input**: Leave the checkbox unchecked to execute the workflow without input (sends `null`)
- **Structured Input**: Check the checkbox to reveal the full input form with all workflow parameters
- **Smart Validation**: Form validation only applies when the checkbox is checked and input is being provided

**How It Works:**

1. Select a workflow with optional input (e.g., `awa-201-generate-documentation-site`)
2. By default, the "Override Defaults" checkbox is unchecked and the form is hidden
3. The Execute button is enabled immediately - you can run the workflow without providing input
4. Check "Override Defaults" to see and fill the structured input form
5. Form validation applies only when providing input

**Benefits:**

- Clearer user experience for workflows that accept optional input
- No need to interact with complex forms when default behavior is desired
- Full control when custom input is needed

**Technical Details:**

- Backend: Workflows with nullable parameters (e.g., `param: Type | None` or `param: Type | SkipJsonSchema[None]`) automatically include the `x-nullable-input` flag in their JSON Schema
- Frontend: The UI detects this flag and renders the checkbox control
- API: No changes to the API contract - continues to accept empty string `""` for null input and JSON strings for structured input
