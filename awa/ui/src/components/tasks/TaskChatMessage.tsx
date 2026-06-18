import { Box, ListItem, ListItemText, Avatar, Typography } from '@mui/material';
import { Person as PersonIcon, SmartToy as BotIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import type { HITLChatMessage } from '@/types/api_models';

interface TaskChatMessageProps {
    message: HITLChatMessage;
}

const TaskChatMessage = ({ message }: TaskChatMessageProps) => {
    const getMessageIcon = () => {
        if (message.isHuman) {
            return <PersonIcon />;
        }
        return <BotIcon />;
    };

    const getMessageColor = () => {
        if (message.isHuman) {
            return 'grey.100';
        }
        return 'transparent';
    };

    return (
        <ListItem sx={{ alignItems: 'flex-start', bgcolor: getMessageColor() }}>
            <Avatar
                sx={{
                    mr: 2,
                    bgcolor: message.isHuman ? 'primary.main' : 'secondary.main'
                }}
            >
                {getMessageIcon()}
            </Avatar>
            <ListItemText
                primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle2">
                            {message.isHuman ? 'You' : 'System'}
                        </Typography>
                        {message.timestamp && (
                            <Typography variant="caption" color="text.secondary">
                                {format(new Date(message.timestamp), 'HH:mm')}
                            </Typography>
                        )}
                    </Box>
                }
                secondary={
                    <Typography
                        variant="body2"
                        sx={{
                            mt: 0.5,
                            whiteSpace: 'pre-line',
                            wordBreak: 'break-word'
                        }}
                    >
                        {message.message}
                    </Typography>
                }
            />
        </ListItem>
    );
};

export default TaskChatMessage;
