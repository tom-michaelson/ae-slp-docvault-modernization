import { Box, Typography, Chip, Divider, Stack, IconButton } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import type { AgentStreamingStatusResponse } from '@/types/api_models';


interface AgentSessionDetailsProps {
    sessionStatus?: AgentStreamingStatusResponse;
    onRefresh?: () => void;
}

const AgentSessionDetails = ({
    sessionStatus,
    onRefresh,
}: AgentSessionDetailsProps) => {
    if (!sessionStatus) {
        return null;
    }

    return (
        <Box sx={{ mb: 3, p: 2, backgroundColor: 'background.default', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle1">Session Details</Typography>
                {onRefresh && (
                    <IconButton size="small" onClick={onRefresh}>
                        <Refresh />
                    </IconButton>
                )}
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Session ID:</Typography>
                    <Typography variant="body2" fontFamily="monospace">
                        {sessionStatus.sessionId}
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Active:</Typography>
                    <Chip label={sessionStatus.isActive ? 'Yes' : 'No'} size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Messages:</Typography>
                    <Typography variant="body2">
                        {sessionStatus.messageCount || 0}
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Processing:</Typography>
                    <Chip label={sessionStatus.processingAgent ? 'Yes' : 'No'} size="small" />
                </Box>
            </Stack>
        </Box>
    );
};

export default AgentSessionDetails;
