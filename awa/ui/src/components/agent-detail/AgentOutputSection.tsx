import { Box, Typography, Alert, CircularProgress } from '@mui/material';

interface AgentOutputSectionProps {
    output?: string;
    status: string;
    error?: string;
    isActive: boolean;
    onClearError?: () => void;
}

const AgentOutputSection = ({
    output,
    status,
    error,
    isActive,
    onClearError,
}: AgentOutputSectionProps) => {
    return (
        <Box sx={{ mb: 3 }}>
            {/* Status Messages */}
            {status === 'streaming' && (
                <Alert severity="info" sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <CircularProgress size={20} />
                        <Typography>Agent is processing your prompt...</Typography>
                    </Box>
                </Alert>
            )}

            {status === 'completed' && (
                <Alert severity="success" sx={{ mb: 3 }}>
                    Agent execution completed. The output is shown below.
                </Alert>
            )}

            {/* Error Display */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={onClearError}>
                    <Typography variant="subtitle2">Error:</Typography>
                    {error}
                </Alert>
            )}

            {/* Output Display */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                    Agent Output
                </Typography>
                {isActive && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={16} />
                        <Typography variant="caption">Processing...</Typography>
                    </Box>
                )}
            </Box>

            <Box
                sx={{
                    minHeight: 400,
                    maxHeight: 600,
                    overflow: 'auto',
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    p: 2,
                    backgroundColor: '#f5f5f5',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    whiteSpace: 'pre-wrap',
                }}
            >
                {output || (
                    <Typography variant="body2" color="text.secondary">
                        Agent output will appear here when streaming begins...
                    </Typography>
                )}
            </Box>
        </Box>
    );
};

export default AgentOutputSection;
