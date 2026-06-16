import { Box, Typography, IconButton, Chip } from '@mui/material';
import { Minimize, Circle } from '@mui/icons-material';

interface ChatHeaderProps {
    isConnected: boolean;
    onClose: () => void;
}

const ChatHeader = ({ isConnected, onClose }: ChatHeaderProps) => {
    return (
        <Box
            sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                p: 2,
                borderBottom: 1,
                borderColor: 'divider',
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                borderTopLeftRadius: 12,
                borderTopRightRadius: 12,
            }}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 500 }}>
                    Chat
                </Typography>
                <Chip
                    size="small"
                    icon={
                        <Circle
                            sx={{
                                fontSize: 10,
                                color: isConnected ? 'success.main' : 'error.main'
                            }}
                        />
                    }
                    label={isConnected ? 'Connected' : 'Disconnected'}
                    sx={{
                        backgroundColor: 'rgba(255, 255, 255, 0.2)',
                        color: 'primary.contrastText',
                        '& .MuiChip-icon': {
                            marginLeft: '4px',
                        }
                    }}
                />
            </Box>
            <Box>
                <IconButton
                    size="small"
                    onClick={onClose}
                    sx={{ color: 'primary.contrastText' }}
                >
                    <Minimize />
                </IconButton>
            </Box>
        </Box>
    );
};

export default ChatHeader;
