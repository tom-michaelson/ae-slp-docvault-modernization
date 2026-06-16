import { useState, useEffect, useCallback } from 'react';
import { hitlChatSocket, type HITLSocketMessage } from '@/services/chatSocket';
import type { HITLChatMessage } from '@/types/api_models';

interface UseHitlChatOptions {
    taskId: string;
    initialMessages?: HITLChatMessage[];
    autoConnect?: boolean;
}

interface UseHitlChatReturn {
    messages: HITLChatMessage[];
    isConnected: boolean;
    isInRoom: boolean;
    sendMessage: (message: string, userInfo?: Record<string, any>) => Promise<void>;
    clearMessages: () => void;
    joinRoom: () => Promise<void>;
    leaveRoom: () => Promise<void>;
}

/**
 * Hook for managing HITL chat functionality
 * Handles WebSocket connection, room management, and message handling
 */
export const useHitlChat = ({
    taskId,
    initialMessages = [],
    autoConnect = true,
}: UseHitlChatOptions): UseHitlChatReturn => {
    const [messages, setMessages] = useState<HITLChatMessage[]>(initialMessages);
    const [isConnected, setIsConnected] = useState(false);
    const [isInRoom, setIsInRoom] = useState(false);

    // Initialize messages from props
    useEffect(() => {
        if (initialMessages && initialMessages.length > 0) {
            setMessages(initialMessages);
        }
    }, [initialMessages]);

    // Handle WebSocket connection and room joining
    useEffect(() => {
        if (!autoConnect) return;

        // Connect to socket
        hitlChatSocket.connect();

        // Track connection status
        const unsubscribeConnection = hitlChatSocket.onConnectionChange((connected) => {
            setIsConnected(connected);

            // Auto-rejoin room on reconnection if we were in it
            if (connected && isInRoom && !hitlChatSocket.isInRoom(taskId)) {
                joinRoom();
            }
        });

        // Set initial connection state
        setIsConnected(hitlChatSocket.isConnected());

        // Handle incoming messages for this task
        const unsubscribeMessage = hitlChatSocket.onTaskMessage(taskId, (socketMessage: HITLSocketMessage) => {
            const chatMessage: HITLChatMessage = {
                message: socketMessage.message,
                timestamp: new Date(socketMessage.timestamp),
                isHuman: socketMessage.is_human,
                data: socketMessage.data,
            };

            setMessages(prev => [...prev, chatMessage]);
        });

        // Auto-join room if connected
        if (hitlChatSocket.isConnected()) {
            joinRoom();
        }

        return () => {
            unsubscribeConnection();
            unsubscribeMessage();
            // Note: We don't leave the room here to allow for component remounting
            // The room will be left when explicitly called or when the socket disconnects
        };
    }, [taskId, autoConnect]);

    /**
     * Join the HITL chat room for this task
     */
    const joinRoom = useCallback(async () => {
        if (!hitlChatSocket.isConnected()) {
            console.warn('[useHitlChat] Cannot join room - not connected');
            return;
        }

        try {
            await hitlChatSocket.joinHitlChat(taskId);
            setIsInRoom(true);
        } catch (error) {
            console.error('[useHitlChat] Failed to join room:', error);
            setIsInRoom(false);
            throw error;
        }
    }, [taskId]);

    /**
     * Leave the HITL chat room for this task
     */
    const leaveRoom = useCallback(async () => {
        try {
            await hitlChatSocket.leaveHitlChat(taskId);
            setIsInRoom(false);
        } catch (error) {
            console.error('[useHitlChat] Failed to leave room:', error);
            // Still mark as left since we tried
            setIsInRoom(false);
        }
    }, [taskId]);

    /**
     * Send a message to the HITL chat
     */
    const sendMessage = useCallback(async (message: string, userInfo?: Record<string, any>) => {
        if (!message.trim()) {
            throw new Error('Message cannot be empty');
        }

        if (!isConnected) {
            throw new Error('Not connected to chat server');
        }

        if (!isInRoom) {
            throw new Error('Not in chat room');
        }

        try {
            await hitlChatSocket.sendHitlChatMessage(taskId, message.trim(), userInfo || {});

            // Note: We don't optimistically add the message here because
            // it will come back through the socket with proper server timestamp
        } catch (error) {
            console.error('[useHitlChat] Failed to send message:', error);
            throw error;
        }
    }, [taskId, isConnected, isInRoom]);

    /**
     * Clear all messages (local only, doesn't affect server)
     */
    const clearMessages = useCallback(() => {
        setMessages([]);
    }, []);

    return {
        messages,
        isConnected,
        isInRoom,
        sendMessage,
        clearMessages,
        joinRoom,
        leaveRoom,
    };
};

/**
 * Hook for managing multiple HITL chat subscriptions
 * Useful for monitoring multiple tasks simultaneously
 */
export const useMultipleHitlChats = (taskIds: string[]) => {
    const [messagesMap, setMessagesMap] = useState<Map<string, HITLChatMessage[]>>(new Map());
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        if (taskIds.length === 0) return;

        // Connect to socket
        hitlChatSocket.connect();

        // Track connection status
        const unsubscribeConnection = hitlChatSocket.onConnectionChange(setIsConnected);

        // Set initial connection state
        setIsConnected(hitlChatSocket.isConnected());

        // Join all rooms and set up message handlers
        const unsubscribers: (() => void)[] = [];

        taskIds.forEach(taskId => {
            // Join room
            if (hitlChatSocket.isConnected()) {
                hitlChatSocket.joinHitlChat(taskId).catch(console.error);
            }

            // Handle messages
            const unsubscribe = hitlChatSocket.onTaskMessage(taskId, (socketMessage: HITLSocketMessage) => {
                const chatMessage: HITLChatMessage = {
                    message: socketMessage.message,
                    timestamp: new Date(socketMessage.timestamp),
                    isHuman: socketMessage.is_human,
                    data: socketMessage.data,
                };

                setMessagesMap(prev => {
                    const newMap = new Map(prev);
                    const existing = newMap.get(taskId) || [];
                    newMap.set(taskId, [...existing, chatMessage]);
                    return newMap;
                });
            });

            unsubscribers.push(unsubscribe);
        });

        return () => {
            unsubscribeConnection();
            unsubscribers.forEach(fn => fn());

            // Leave all rooms
            taskIds.forEach(taskId => {
                hitlChatSocket.leaveHitlChat(taskId).catch(console.error);
            });
        };
    }, [taskIds.join(',')]); // Re-run when task list changes

    return {
        messagesMap,
        isConnected,
        getMessages: (taskId: string) => messagesMap.get(taskId) || [],
    };
};
