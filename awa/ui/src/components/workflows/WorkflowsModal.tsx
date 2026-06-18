import { useEffect, useState, useRef } from 'react';
import Modal from '@mui/material/Modal';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close'
import { createAjv, type JsonFormsCore } from '@jsonforms/core';
import {
  materialCells,
  materialRenderers,
} from '@jsonforms/material-renderers';
import { JsonForms } from '@jsonforms/react';
import type { ErrorObject } from 'ajv';
import Box from '@mui/material/Box';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import { useGetAvailableWorkflows, useRunWorkflowMutation } from '@/queries/workflow';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import { IconButton } from '@mui/material';
import { testId } from '@/utils/constants';
import type { WorkflowInfo } from '@/types';

interface WorkflowsModalProps {
    open: boolean;
    onClose: () => void;
}


const WorkflowsModal = ({ open, onClose }: WorkflowsModalProps) => {
    const { data: workflowsRaw, isLoading: isGetAvailableLoading } = useGetAvailableWorkflows();
    const { mutate, isSuccess, isLoading: isMutationLoading } = useRunWorkflowMutation();

    // Deduplicate workflows by name (keep first occurrence)
    const workflows = workflowsRaw ? Array.from(
        new Map(workflowsRaw.map(w => [w.name, w])).values()
    ) : undefined;

    const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowInfo | null>(
        workflows ? workflows[0] : null
    );
    const [payload, setPayload] = useState({});
    const [isSubmittable, setIsSubmittable] = useState<boolean>(false);
    const [inputErrors, setInputErrors] = useState<ErrorObject[]>([]);
    const [overrideDefaults, setoverrideDefaults] = useState<boolean>(false);
    const [isNullableInput, setIsNullableInput] = useState<boolean>(false);
    const autocompleteRef = useRef<HTMLDivElement>(null);

    const isLoading = isGetAvailableLoading || isMutationLoading

    const validator = createAjv();

    const handleExecute = () => {
        if (!selectedWorkflow) {
            return;
        }

        // Determine what to send based on nullable input and checkbox
        let inputData = '';
        if (isNullableInput && !overrideDefaults) {
            // Send empty string when nullable and checkbox is unchecked
            inputData = '';
        } else if (Object.keys(payload).length !== 0) {
            // Send JSON payload when input is provided
            inputData = JSON.stringify(payload);
        }

        mutate({
            name: selectedWorkflow?.name,
            input: inputData,
        })
    };

    const handlePayloadChange = ({ data }: Pick<JsonFormsCore, 'data' | 'errors'>) => {
        if (selectedWorkflow === null) {
            return;
        }
        setPayload(data);

        // Only validate if we're providing input (or input is not nullable)
        if (!isNullableInput || overrideDefaults) {
            const validate = validator.compile(selectedWorkflow?.parameters);
            setIsSubmittable(validate(data));
        }
    }

    useEffect(() => {
        const schema = selectedWorkflow?.parameters;
        setPayload({});

        // Check if input is nullable
        const nullable = schema?.['x-nullable-input'] === true;
        setIsNullableInput(nullable);

        // Reset checkbox when workflow changes
        setoverrideDefaults(false);

        const requiredFields = schema?.required;
        // If nullable and unchecked, allow submission
        // If not nullable, use existing logic
        if (nullable) {
            setIsSubmittable(true);
        } else {
            setIsSubmittable(!(requiredFields && requiredFields.length > 0));
        }

        setInputErrors([]);
    }, [selectedWorkflow])

    // Separate effect to handle validation when overrideDefaults changes
    useEffect(() => {
        const schema = selectedWorkflow?.parameters;
        const requiredFields = schema?.required;

        // Update submittable state based on checkbox state
        if (isNullableInput && !overrideDefaults) {
            // Nullable and unchecked - allow submission
            setIsSubmittable(true);
        } else if (isNullableInput && overrideDefaults) {
            // Nullable and checked - check if form has required fields
            setIsSubmittable(!(requiredFields && requiredFields.length > 0));
        }
    }, [overrideDefaults, isNullableInput, selectedWorkflow])

    useEffect(() => {
        if (isSuccess) {
            onClose();
        }
    }, [isSuccess])

    useEffect(() => {
        if (!open) {
            // Clear form data when modal closes
            setSelectedWorkflow(null);
        } else {
            // Focus the Autocomplete input when modal opens
            // Use setTimeout to ensure the modal is fully rendered
            setTimeout(() => {
                const inputElement = autocompleteRef.current?.querySelector('input');
                if (inputElement) {
                    inputElement.focus();
                }
            }, 100);
        }
    }, [open])

    return (
        <Modal open={open} onClose={onClose}>
            <Box
                data-testid={testId.modal.container}
                sx={{
                position: 'absolute',
                left: '10vw',
                top: '10vh',
                bgcolor: 'background.paper',
                width: '80vw',
                height: '80vh',
                overflowY: 'scroll',
                padding: 4
                }}
            >
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant='h4'>Execute Workflow</Typography>
                    <IconButton onClick={onClose} data-testid={testId.modal.closeButton}>
                        <CloseIcon />
                    </IconButton>
                </Box>
                <Box sx={{ pt: 4, display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <Autocomplete
                        ref={autocompleteRef}
                        value={selectedWorkflow}
                        options={workflows ?? []}
                        getOptionLabel={(option) => {
                            if (typeof option === 'string') return option;
                            const workflow = option as WorkflowInfo;
                            return workflow.description
                                ? `${workflow.name} - ${workflow.description}`
                                : workflow.name;
                        }}
                        renderInput={(params) => <TextField {...params} label="Workflow" />}
                        data-testid={testId.modal.workflowSelect}
                        slotProps={{
                            popper: {
                                'data-testid': testId.modal.dropdownMenu,
                            },
                        }}
                        onChange={(_e, newValue) => {
                            setSelectedWorkflow(newValue);
                        }}
                        isOptionEqualToValue={(option, value) => {
                            if (!option || !value) return false;
                            return option.name === value.name;
                        }}
                        disableClearable={false}
                    />
                    {/* Checkbox for nullable input workflows */}
                    {isNullableInput && (
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={overrideDefaults}
                                    onChange={(e) => setoverrideDefaults(e.target.checked)}
                                    data-testid={testId.modal.overrideDefaultsCheckbox}
                                />
                            }
                            label="Override Defaults"
                        />
                    )}
                    {/* Only show form if input is required OR (nullable AND checkbox is checked) */}
                    {selectedWorkflow?.parameters &&
                     Object.keys(selectedWorkflow?.parameters).length > 0 &&
                     (!isNullableInput || overrideDefaults) && (
                        <Box data-testid={testId.modal.jsonForms}>
                            <JsonForms
                                schema={selectedWorkflow?.parameters}
                                data={payload}
                                renderers={materialRenderers}
                                cells={materialCells}
                                onChange={handlePayloadChange}
                                validationMode={'ValidateAndHide'}
                                additionalErrors={inputErrors}
                            />
                        </Box>
                    )}
                    <Button
                        variant='contained'
                        color='primary'
                        onClick={handleExecute}
                        data-testid={testId.modal.executeButton}
                        disabled={!isSubmittable || isLoading}
                    >
                        Execute
                    </Button>
                </Box>
            </Box>
        </Modal>
    );
};

export default WorkflowsModal;
