// Data-TestIds
const testIdPrefixes = {
    panel: 'WorkflowPanel',
    modal: 'WorkflowModal',
    listing: 'WorkflowListing',
    statusBadge: 'WorkflowStatusBadge',
    tasks: 'Tasks',
};

export const testId = {
    panel: {
        newRunButton: `${testIdPrefixes.panel}-new-run-button`,
    },
    modal: {
        closeButton: `${testIdPrefixes.modal}-close-button`,
        executeButton: `${testIdPrefixes.modal}-execute-button`,
        workflowSelect: `${testIdPrefixes.modal}-workflow-select`,
        container: `${testIdPrefixes.modal}-container`,
        dropdownMenu: `${testIdPrefixes.modal}-dropdown-menu`,
        jsonForms: `${testIdPrefixes.modal}-json-forms`,
        nameInput: `${testIdPrefixes.modal}-name-input`,
        overrideDefaultsCheckbox: `${testIdPrefixes.modal}-provide-input-checkbox`,
    },
    listing: {
        runListing: `${testIdPrefixes.listing}-workflow-run`,
    },
    tasks: {
        taskListing: `${testIdPrefixes.tasks}-listing`,
    },
    statusBadge: {
        badge: `${testIdPrefixes.statusBadge}-badge`,
    }
}
