import { Box, Typography, Paper } from '@mui/material';
import { format } from 'date-fns';
import type { ChatMessage as ChatMessageType } from '@/types/chat';

interface ChatMessageProps {
    message: ChatMessageType;
}

const ChatMessage = ({ message }: ChatMessageProps) => {
    const isUser = message.sender === 'user';
    const isAgent = message.sender === 'agent';
    const isSystem = message.sender === 'system';

    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: isUser ? 'flex-end' : 'flex-start',
                mb: 1.5,
            }}
        >
            <Paper
                elevation={1}
                sx={{
                    maxWidth: '70%',
                    px: 2,
                    py: 1,
                    backgroundColor: isUser
                        ? 'primary.main'
                        : isSystem
                        ? 'grey.100'
                        : 'background.paper',
                    color: isUser ? 'primary.contrastText' : 'text.primary',
                    borderRadius: 2,
                    borderTopRightRadius: isUser ? 0 : 16,
                    borderTopLeftRadius: isUser ? 16 : 0,
                }}
            >
                {isSystem && (
                    <Typography
                        variant="caption"
                        sx={{
                            display: 'block',
                            fontWeight: 'bold',
                            mb: 0.5,
                            color: 'text.secondary'
                        }}
                    >
                        System
                    </Typography>
                )}
                {isAgent && (
                    <Typography
                        variant="caption"
                        sx={{
                            display: 'block',
                            fontWeight: 'bold',
                            mb: 0.5,
                            color: 'primary.main'
                        }}
                    >
                        Agent
                    </Typography>
                )}
                <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                    {message.content}
                </Typography>
                <Typography
                    variant="caption"
                    sx={{
                        display: 'block',
                        mt: 0.5,
                        opacity: 0.7,
                        color: isUser ? 'primary.contrastText' : 'text.secondary'
                    }}
                >
                    {format(new Date(message.timestamp), 'HH:mm')}
                </Typography>
            </Paper>
        </Box>
    );
};

export default ChatMessage;
