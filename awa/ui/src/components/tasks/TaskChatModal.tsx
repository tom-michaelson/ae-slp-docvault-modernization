import { useState, useEffect, useRef } from 'react';
import {
    Modal,
    Paper,
    Box,
    Typography,
    IconButton,
    TextField,
    Button,
    List,
    Divider,
    Stack,
    Chip,
    CircularProgress,
} from '@mui/material';
import {
    Close as CloseIcon,
    Send as SendIcon,
} from '@mui/icons-material';
import type { HITLTaskDetail, HITLChatMessage } from '@/types/api_models';
import { hitlChatSocket } from '@/services/chatSocket';
import { useTaskSubmissionMutation } from '@/queries/task';
import { getChatHistory, sendUserMessage } from '@/api/task';
import TaskChatMessage from './TaskChatMessage';

interface TaskChatModalProps {
    open: boolean;
    onClose: () => void;
    task: HITLTaskDetail;
}

const TaskChatModal = ({ open, onClose, task }: TaskChatModalProps) => {
    const [messages, setMessages] = useState<HITLChatMessage[]>([]);
    const [currentMessage, setCurrentMessage] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { mutate: submitTask } = useTaskSubmissionMutation(task.id);

    console.log(messages);
    // Fetch latest chat history when modal opens
    useEffect(() => {
        const fetchLatestHistory = async () => {
            if (open) {
                try {
                    console.log('[TaskChatModal] Fetching latest chat history for task:', task.id);
                    const latestHistory = await getChatHistory(task.id);
                    console.log(latestHistory);
                    setMessages(latestHistory);
                    console.log('[TaskChatModal] Loaded', latestHistory.length, 'messages from server');
                } catch (error) {
                    console.warn('[TaskChatModal] Could not fetch latest history, using cached:', error);
                    setMessages(task.chatHistory || []);
                }
            }
        };
        fetchLatestHistory();
    }, [open, task.id, task.chatHistory]);

    // Connect to chat socket when modal opens
    useEffect(() => {
        if (open) {
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
                console.log('???');
                hitlChatSocket.leaveHitlChat(task.id).catch(console.error);
                unsubscribeConnection();
            };
        }
    }, [open, task.id]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!currentMessage.trim()) return;

        try {
            console.log('[TaskChatModal] Sending user message via HTTP API');
            await sendUserMessage(task.id, currentMessage.trim(), {
                userId: 'current_user', // TODO: Get actual user info from auth context
            });
            setCurrentMessage('');
            setMessages(prev => [...prev, {
                    message: currentMessage.trim(),
                    timestamp: new Date(),
                    isHuman: true,
                    data: null,
                }])
            console.log('[TaskChatModal] User message sent successfully');
        } catch (error) {
            console.error('[TaskChatModal] Failed to send message:', error);
            // TODO: Add user-facing error notification (toast, snackbar, etc.)
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
            onClose();
        } catch (error) {
            console.error('Failed to complete task:', error);
        } finally {
            setIsSubmitting(false);
        }
    };


    return (
        <Modal open={open} onClose={onClose}>
            <Paper
                sx={{
                    position: 'absolute',
                    left: '10vw',
                    top: '5vh',
                    width: '80vw',
                    height: '90vh',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: 2,
                }}
            >
                {/* Header */}
                <Box
                    sx={{
                        p: 2,
                        borderBottom: 1,
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                    }}
                >
                    <Box>
                        <Typography variant="h5" gutterBottom>
                            {task.title}
                        </Typography>
                        <Stack direction="row" spacing={1} alignItems="center">
                            <Chip
                                size="small"
                                label="Chat Mode"
                                color="primary"
                                variant="outlined"
                            />
                            <Chip
                                size="small"
                                label={isConnected ? 'Connected' : 'Disconnected'}
                                color={isConnected ? 'success' : 'error'}
                                variant="outlined"
                            />
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                            Task ID: {task.id}
                        </Typography>
                    </Box>
                    <IconButton onClick={onClose}>
                        <CloseIcon />
                    </IconButton>
                </Box>

                {/* Task Description */}
                {task.description && (
                    <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Typography variant="body2" color="text.secondary">
                            {task.description}
                        </Typography>
                    </Box>
                )}

                {/* Messages */}
                <Box
                    sx={{
                        flex: 1,
                        overflowY: 'auto',
                        p: 1,
                    }}
                >
                    <List>
                        {messages.map((message, index) => (
                            <TaskChatMessage key={index} message={message} />
                        ))}
                        <div ref={messagesEndRef} />
                    </List>
                </Box>

                <Divider />

                {/* Input Area */}
                <Box sx={{ p: 2 }}>
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
            </Paper>
        </Modal>
    );
};

export default TaskChatModal;
