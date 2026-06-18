import { useEffect, useRef } from 'react';
import { Box, Typography } from '@mui/material';
import ChatMessage from './ChatMessage';
import type { ChatMessage as ChatMessageType } from '@/types/chat';

interface ChatMessagesProps {
    messages: ChatMessageType[];
}

const ChatMessages = ({ messages }: ChatMessagesProps) => {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <Box
            ref={scrollRef}
            sx={{
                flex: 1,
                overflowY: 'auto',
                p: 2,
                backgroundColor: 'grey.50',
                minHeight: 300,
                maxHeight: 400,
            }}
        >
            {messages.length === 0 ? (
                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100%',
                        minHeight: 300,
                    }}
                >
                    <Typography variant="body2" color="text.secondary">
                        No messages yet. Start a conversation!
                    </Typography>
                </Box>
            ) : (
                messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                ))
            )}
        </Box>
    );
};

export default ChatMessages;
