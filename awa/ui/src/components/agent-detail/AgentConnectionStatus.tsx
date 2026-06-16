import { Box, Typography, Chip } from '@mui/material';
import { Circle } from '@mui/icons-material';

interface AgentConnectionStatusProps {
    isConnected: boolean;
    status: string;
    sessionId?: string;
}

const AgentConnectionStatus = ({
    isConnected,
    status,
    sessionId,
}: AgentConnectionStatusProps) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'idle': return 'default';
            case 'connecting': return 'warning';
            case 'streaming': return 'primary';
            case 'completed': return 'success';
            case 'error': return 'error';
            default: return 'default';
        }
    };

    return (
        <Box sx={{ mb: 3, p: 2, backgroundColor: 'background.default', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="subtitle1">Connection Status:</Typography>
                    <Chip
                        icon={
                            <Circle
                                sx={{
                                    fontSize: 12,
                                    color: isConnected ? 'success.main' : 'error.main'
                                }}
                            />
                        }
                        label={isConnected ? 'Connected' : 'Disconnected'}
                        color={isConnected ? 'success' : 'error'}
                        size="small"
                    />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2">Stream Status:</Typography>
                    <Chip
                        label={status}
                        color={getStatusColor(status) as any}
                        size="small"
                    />
                    {sessionId && (
                        <Typography variant="caption" sx={{ ml: 1 }}>
                            Session: {sessionId.slice(0, 8)}...
                        </Typography>
                    )}
                </Box>
            </Box>
        </Box>
    );
};

export default AgentConnectionStatus;
