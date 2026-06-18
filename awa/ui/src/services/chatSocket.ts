import { io, Socket } from 'socket.io-client';
import type { HITLChatMessage } from '@/types/api_models';

export interface HITLSocketMessage {
    task_id: string;
    message: string;
    data?: any;
    timestamp: string;
    is_human: boolean;
    user_info?: Record<string, any>;
}

/**
 * Service for managing HITL chat WebSocket connections.
 * Handles real-time communication for Human-in-the-Loop task interactions.
 */
class HITLChatSocketService {
    private socket: Socket | null = null;
    private messageHandlers: Map<string, Set<(message: HITLSocketMessage) => void>> = new Map();
    private connectionHandlers: Set<(connected: boolean) => void> = new Set();
    private activeRooms: Set<string> = new Set();

    /**
     * Connect to the Socket.IO server
     * @param url Optional custom URL, defaults to API server URL
     */
    connect(url?: string) {
        if (this.socket?.connected) {
            return;
        }

        const socketUrl = url || import.meta.env.PUBLIC_API_URL || 'http://localhost:8001';

        this.socket = io(socketUrl, {
            path: '/socket.io/',
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });

        this.socket.on('connect', () => {
            console.log('[HITLChatSocket] Connected to server');
            this.connectionHandlers.forEach(handler => handler(true));

            // Rejoin all active rooms on reconnection
            this.activeRooms.forEach(taskId => {
                this.joinHitlChat(taskId).catch(console.error);
            });
        });

        this.socket.on('disconnect', () => {
            console.log('[HITLChatSocket] Disconnected from server');
            this.connectionHandlers.forEach(handler => handler(false));
        });

        this.socket.on('connect_error', (err) => {
            console.log('Error connecting...', err);
        });

        // Listen for HITL chat messages
        this.socket.on('hitl_chat_message', (message: HITLSocketMessage) => {
            const handlers = this.messageHandlers.get(message.task_id);
            if (handlers) {
                handlers.forEach(handler => handler(message));
            }
        })
    }

    /**
     * Disconnect from the Socket.IO server and cleanup
     */
    disconnect() {
        this.activeRooms.clear();
        this.messageHandlers.clear();
        this.connectionHandlers.clear();
        this.socket?.disconnect();
        this.socket = null;
    }

    /**
     * Join a HITL task chat room to receive real-time messages
     * @param taskId The HITL task ID to join
     */
    async joinHitlChat(taskId: string): Promise<void> {
        if (!this.socket?.connected) {
            throw new Error('Socket not connected');
        }

        return new Promise((resolve, reject) => {
            this.socket!.emit('join_hitl_chat', { task_id: taskId }, (response: any) => {
                if (response?.status === 'joined') {
                    this.activeRooms.add(taskId);
                    console.log(`[HITLChatSocket] Joined chat room for task ${taskId}`);
                    resolve();
                } else {
                    const errorMsg = response?.message || 'Failed to join chat room';
                    console.error(`[HITLChatSocket] Failed to join task ${taskId}:`, errorMsg);
                    reject(new Error(errorMsg));
                }
            });
        });
    }

    /**
     * Leave a HITL task chat room
     * @param taskId The HITL task ID to leave
     */
    async leaveHitlChat(taskId: string): Promise<void> {
        if (!this.socket?.connected) {
            // Not an error - just cleanup state
            this.activeRooms.delete(taskId);
            this.messageHandlers.delete(taskId);
            return;
        }

        return new Promise((resolve, reject) => {
            this.socket!.emit('leave_hitl_chat', { task_id: taskId }, (response: any) => {
                this.activeRooms.delete(taskId);
                this.messageHandlers.delete(taskId);

                if (response?.status === 'left') {
                    console.log(`[HITLChatSocket] Left chat room for task ${taskId}`);
                    resolve();
                } else {
                    // Still resolve since we've cleaned up locally
                    console.warn(`[HITLChatSocket] Leave response unexpected:`, response);
                    resolve();
                }
            });
        });
    }

    /**
     * Send a chat message to a HITL task room
     * @param taskId The HITL task ID
     * @param message The message content
     * @param userInfo Optional user information
     */
    async sendHitlChatMessage(taskId: string, message: string, userInfo: Record<string, any> = {}): Promise<void> {
        if (!this.socket?.connected) {
            throw new Error('Socket not connected');
        }

        return new Promise((resolve, reject) => {
            this.socket!.emit('send_hitl_chat_message', {
                task_id: taskId,
                message: message,
                user_info: userInfo,
            }, (response: any) => {
                if (response?.status === 'sent') {
                    console.log(`[HITLChatSocket] Message sent for task ${taskId}`);
                    resolve();
                } else {
                    const errorMsg = response?.message || 'Failed to send message';
                    console.error(`[HITLChatSocket] Failed to send message:`, errorMsg);
                    reject(new Error(errorMsg));
                }
            });
        });
    }

    /**
     * Register a handler for messages in a specific task room
     * @param taskId The HITL task ID to listen to
     * @param handler Function to handle incoming messages
     * @returns Cleanup function to remove the handler
     */
    onTaskMessage(taskId: string, handler: (message: HITLSocketMessage) => void) {
        if (!this.messageHandlers.has(taskId)) {
            this.messageHandlers.set(taskId, new Set());
        }
        this.messageHandlers.get(taskId)!.add(handler);

        return () => {
            const handlers = this.messageHandlers.get(taskId);
            if (handlers) {
                handlers.delete(handler);
                if (handlers.size === 0) {
                    this.messageHandlers.delete(taskId);
                }
            }
        };
    }

    /**
     * Register a handler for connection state changes
     * @param handler Function to handle connection state changes
     * @returns Cleanup function to remove the handler
     */
    onConnectionChange(handler: (connected: boolean) => void) {
        this.connectionHandlers.add(handler);
        return () => this.connectionHandlers.delete(handler);
    }

    /**
     * Check if currently connected to the server
     */
    isConnected(): boolean {
        return this.socket?.connected ?? false;
    }

    /**
     * Check if currently in a specific task room
     */
    isInRoom(taskId: string): boolean {
        return this.activeRooms.has(taskId);
    }
}

export const hitlChatSocket = new HITLChatSocketService();

// For backward compatibility, export as chatSocket too
export const chatSocket = hitlChatSocket;
