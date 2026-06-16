import { useState, useEffect, useRef } from 'react';
import {
    Box,
    TextField,
    Button,
    List,
    Divider,
    Stack,
    Chip,
    CircularProgress,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import type { HITLTaskDetail, HITLChatMessage } from '@/types/api_models';
import { hitlChatSocket } from '@/services/chatSocket';
import { useTaskSubmissionMutation } from '@/queries/task';
import { getChatHistory, sendUserMessage } from '@/api/task';
import TaskChatMessage from './TaskChatMessage';

interface TaskChatEmbedProps {
    task: HITLTaskDetail;
    onComplete: () => void;
}

const TaskChatEmbed = ({ task, onComplete }: TaskChatEmbedProps) => {
    const [messages, setMessages] = useState<HITLChatMessage[]>([]);
    const [currentMessage, setCurrentMessage] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { mutate: submitTask } = useTaskSubmissionMutation(task.id);

    // Fetch latest chat history when component mounts
    useEffect(() => {
        const fetchLatestHistory = async () => {
            try {
                console.log('[TaskChatEmbed] Fetching latest chat history for task:', task.id);
                const latestHistory = await getChatHistory(task.id);
                setMessages(latestHistory);
                console.log('[TaskChatEmbed] Loaded', latestHistory.length, 'messages from server');
            } catch (error) {
                console.warn('[TaskChatEmbed] Could not fetch latest history, using cached:', error);
                setMessages(task.chatHistory || []);
            }
        };
        fetchLatestHistory();
    }, [task.id, task.chatHistory]);

    // Connect to chat socket
    useEffect(() => {
        hitlChatSocket.connect();

        // Set up connection handler
        const unsubscribeConnection = hitlChatSocket.onConnectionChange(setIsConnected);

        // Join the HITL chat room
        const joinChat = async () => {
            try {
                await hitlChatSocket.joinHitlChat(task.id);
            } catch (error) {
                console.error('Failed to join HITL chat:', error);
            }
        };

        // Join immediately if already connected, otherwise wait for connection
        if (hitlChatSocket.isConnected()) {
            joinChat();
        } else {
            const waitForConnection = hitlChatSocket.onConnectionChange((connected) => {
                if (connected) {
                    joinChat();
                    waitForConnection(); // Cleanup the listener
                }
            });
        }

        return () => {
            // Cleanup: leave the chat room and remove listeners
            hitlChatSocket.leaveHitlChat(task.id).catch(console.error);
            unsubscribeConnection();
        };
    }, [task.id]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!currentMessage.trim()) return;

        try {
            console.log('[TaskChatEmbed] Sending user message via HTTP API');
            await sendUserMessage(task.id, currentMessage.trim(), {
                userId: 'current_user', // TODO: Get actual user info from auth context
            });
            setCurrentMessage('');
            setMessages(prev => [...prev, {
                message: currentMessage.trim(),
                timestamp: new Date(),
                isHuman: true,
                data: null,
            }]);
            console.log('[TaskChatEmbed] User message sent successfully');
        } catch (error) {
            console.error('[TaskChatEmbed] Failed to send message:', error);
        }
    };

    const handleKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSendMessage();
        }
    };

    const handleCompleteTask = async () => {
        setIsSubmitting(true);
        try {
            // Submit empty payload to complete the chat task
            submitTask({
                taskId: task.id,
                input: { completed: true }
            });
            onComplete();
        } catch (error) {
            console.error('Failed to complete task:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '500px' }}>
            {/* Connection Status */}
            <Box sx={{ mb: 2 }}>
                <Chip
                    size="small"
                    label={isConnected ? 'Connected' : 'Disconnected'}
                    color={isConnected ? 'success' : 'error'}
                    variant="outlined"
                />
            </Box>

            {/* Messages */}
            <Box
                sx={{
                    flex: 1,
                    overflowY: 'auto',
                    p: 1,
                    bgcolor: 'grey.50',
                    borderRadius: 1,
                    mb: 2,
                }}
            >
                <List>
                    {messages.map((message, index) => (
                        <TaskChatMessage key={index} message={message} />
                    ))}
                    <div ref={messagesEndRef} />
                </List>
            </Box>

            <Divider sx={{ mb: 2 }} />

            {/* Input Area */}
            <Stack spacing={2}>
                <TextField
                    fullWidth
                    multiline
                    minRows={2}
                    maxRows={4}
                    placeholder="Type your message..."
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    variant="outlined"
                />

                <Stack direction="row" spacing={2} justifyContent="flex-end">
                    <Button
                        variant="outlined"
                        color="secondary"
                        onClick={handleCompleteTask}
                        disabled={isSubmitting}
                        startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
                    >
                        {isSubmitting ? 'Completing...' : 'Complete Task'}
                    </Button>
                    <Button
                        variant="contained"
                        endIcon={<SendIcon />}
                        onClick={handleSendMessage}
                        disabled={!currentMessage.trim()}
                    >
                        Send
                    </Button>
                </Stack>
            </Stack>
        </Box>
    );
};

export default TaskChatEmbed;
