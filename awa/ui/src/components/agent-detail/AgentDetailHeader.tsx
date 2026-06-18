import { Box, Typography, IconButton } from '@mui/material';
import { ArrowBack } from '@mui/icons-material';

interface AgentDetailHeaderProps {
    workflowId: string;
}

const AgentDetailHeader = ({ workflowId }: AgentDetailHeaderProps) => {
    return (
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton onClick={() => window.history.back()}>
                <ArrowBack />
            </IconButton>
            <Box sx={{ flex: 1 }}>
                <Typography variant="h4" component="h1" fontWeight="light">
                    Agent Execution Details
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Workflow ID: {workflowId}
                </Typography>
            </Box>
        </Box>
    );
};

export default AgentDetailHeader;
