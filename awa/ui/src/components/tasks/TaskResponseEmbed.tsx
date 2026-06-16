import { useEffect, useState } from 'react';
import {
    Button,
    Typography,
    Box,
    CircularProgress,
} from '@mui/material';
import { createAjv, type JsonFormsCore } from '@jsonforms/core';
import {
    materialCells,
    materialRenderers,
} from '@jsonforms/material-renderers';
import { JsonForms } from '@jsonforms/react';
import type { ErrorObject } from 'ajv';
import { navigate } from 'astro:transitions/client';
import type { HITLTaskDetail } from '@/types/api_models';
import { useTaskSubmissionMutation } from '@/queries/task';

interface TaskResponseEmbedProps {
    task: HITLTaskDetail;
    onComplete: () => void;
}

const TaskResponseEmbed = ({ task, onComplete }: TaskResponseEmbedProps) => {
    const [payload, setPayload] = useState({});
    const [isSubmittable, setIsSubmittable] = useState<boolean>(false);
    const { mutate, isSuccess, isLoading: isMutationLoading } = useTaskSubmissionMutation(task.id);
    const [inputErrors, setInputErrors] = useState<ErrorObject[]>([]);

    const validator = createAjv();

    const handleSubmit = async () => {
        if (!task) {
            return;
        }
        mutate({ taskId: task.id, input: payload });
        onComplete();
    };

    const handlePayloadChange = ({ data }: Pick<JsonFormsCore, 'data' | 'errors'>) => {
        if (!task?.inputSchema) {
            return;
        }
        setPayload(data);
        const validate = validator.compile(task.inputSchema);
        setIsSubmittable(validate(data));
    };

    useEffect(() => {
        if (!task?.inputSchema) {
            setPayload({});
            setIsSubmittable(false);
            setInputErrors([]);
            return;
        }

        const schema = task.inputSchema;
        setPayload({});
        const requiredFields = schema?.required;
        // If task has no required fields, allow submission
        setIsSubmittable(!(requiredFields && requiredFields.length > 0));
        setInputErrors([]);
    }, [task]);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {task.inputSchema ? (
                <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Response Form
                    </Typography>
                    <JsonForms
                        schema={task.inputSchema}
                        data={payload}
                        renderers={materialRenderers}
                        cells={materialCells}
                        onChange={handlePayloadChange}
                        validationMode={'ValidateAndHide'}
                        additionalErrors={inputErrors}
                    />
                </Box>
            ) : (
                <Box sx={{ py: 4, textAlign: 'center' }}>
                    <Typography variant="body1" color="text.secondary">
                        No response schema defined for this task.
                    </Typography>
                </Box>
            )}

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleSubmit}
                    disabled={!isSubmittable || isMutationLoading || !task.inputSchema}
                    startIcon={isMutationLoading ? <CircularProgress size={20} /> : null}
                >
                    {isMutationLoading ? 'Submitting...' : 'Submit Response'}
                </Button>
            </Box>
        </Box>
    );
};

export default TaskResponseEmbed;
