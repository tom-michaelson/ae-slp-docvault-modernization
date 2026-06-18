import { io, Socket } from 'socket.io-client';
import type {
    AgentStreamStartEvent,
    AgentStreamOutputEvent,
    AgentStreamCompleteEvent,
    AgentStreamErrorEvent,
    AgentStreamHistoryEvent,
    AgentStreamMessageEvent,
    AgentStreamStepEvent,
} from '@/lib/socketio';

export type AgentStreamEvent =
    | AgentStreamStartEvent
    | AgentStreamOutputEvent
    | AgentStreamCompleteEvent
    | AgentStreamErrorEvent
    | AgentStreamMessageEvent
    | AgentStreamStepEvent;

/**
 * Service for managing Agent Streaming WebSocket connections.
 * Handles real-time communication for agent execution streaming.
 *
 * Similar to HITLChatSocketService but for agent streaming events.
 */
class AgentStreamSocketService {
    private socket: Socket | null = null;
    private eventHandlers: Map<string, Set<(event: AgentStreamEvent) => void>> = new Map();
    private historyHandlers: Map<string, Set<(event: AgentStreamHistoryEvent) => void>> = new Map();
    private connectionHandlers: Set<(connected: boolean) => void> = new Set();
    private activeStreams: Set<string> = new Set();

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
            console.log('[AgentStreamSocket] Connected to server');
            this.connectionHandlers.forEach(handler => handler(true));

            // Rejoin all active streams on reconnection
            this.activeStreams.forEach(sessionId => {
                this.subscribeToAgentStream(sessionId).catch(console.error);
            });
        });

        this.socket.on('disconnect', () => {
            console.log('[AgentStreamSocket] Disconnected from server');
            this.connectionHandlers.forEach(handler => handler(false));
        });

        this.socket.on('connect_error', (err) => {
            console.log('[AgentStreamSocket] Connection error:', err);
        });

        // Listen for all agent stream events
        this.socket.on('agent_stream_start', (event: AgentStreamStartEvent) => {
            this.notifyEventHandlers(event.session_id, event);
        });

        this.socket.on('agent_stream_output', (event: AgentStreamOutputEvent) => {
            this.notifyEventHandlers(event.session_id, event);
        });

        this.socket.on('agent_stream_message', (event: AgentStreamMessageEvent) => {
            this.notifyEventHandlers(event.session_id, event);
        });

        this.socket.on('agent_stream_step', (event: AgentStreamStepEvent) => {
            this.notifyEventHandlers(event.session_id, event);
        });

        this.socket.on('agent_stream_complete', (event: AgentStreamCompleteEvent) => {
            this.notifyEventHandlers(event.session_id, event);
        });

        this.socket.on('agent_stream_error', (event: AgentStreamErrorEvent) => {
            this.notifyEventHandlers(event.session_id, event);
        });

        this.socket.on('agent_stream_history', (event: AgentStreamHistoryEvent) => {
            console.log('[AgentStreamSocket] Received history event:', event);
            const handlers = this.historyHandlers.get(event.session_id);
            console.log('[AgentStreamSocket] History handlers for', event.session_id, ':', handlers?.size || 0);
            if (handlers) {
                handlers.forEach(handler => handler(event));
            } else {
                console.warn('[AgentStreamSocket] No history handlers registered for', event.session_id);
            }
        });
    }

    /**
     * Notify all event handlers for a specific session
     */
    private notifyEventHandlers(sessionId: string, event: AgentStreamEvent) {
        const handlers = this.eventHandlers.get(sessionId);
        if (handlers) {
            handlers.forEach(handler => handler(event));
        }
    }

    /**
     * Disconnect from the Socket.IO server and cleanup
     */
    disconnect() {
        this.activeStreams.clear();
        this.eventHandlers.clear();
        this.historyHandlers.clear();
        this.connectionHandlers.clear();
        this.socket?.disconnect();
        this.socket = null;
    }

    /**
     * Subscribe to an agent stream session
     * @param sessionId The agent session ID to subscribe to
     */
    async subscribeToAgentStream(sessionId: string): Promise<void> {
        if (!this.socket?.connected) {
            throw new Error('Socket not connected');
        }

        console.log(`[AgentStreamSocket] Attempting to subscribe to ${sessionId}`);

        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                console.error(`[AgentStreamSocket] Subscription timeout for ${sessionId}`);
                reject(new Error('Subscription timeout'));
            }, 5000);

            this.socket!.emit('subscribe_agent_stream', { session_id: sessionId }, (response: any) => {
                clearTimeout(timeout);
                console.log(`[AgentStreamSocket] Received subscription response for ${sessionId}:`, response);

                if (response?.status === 'subscribed') {
                    this.activeStreams.add(sessionId);
                    console.log(`[AgentStreamSocket] Subscribed to stream ${sessionId}`);
                    resolve();
                } else {
                    const errorMsg = response?.message || 'Failed to subscribe to agent stream';
                    console.error(`[AgentStreamSocket] Failed to subscribe to ${sessionId}:`, errorMsg, response);
                    reject(new Error(errorMsg));
                }
            });
        });
    }

    /**
     * Unsubscribe from an agent stream session
     * @param sessionId The agent session ID to unsubscribe from
     */
    async unsubscribeFromAgentStream(sessionId: string): Promise<void> {
        if (!this.socket?.connected) {
            // Not an error - just cleanup state
            this.activeStreams.delete(sessionId);
            this.eventHandlers.delete(sessionId);
            this.historyHandlers.delete(sessionId);
            return;
        }

        return new Promise((resolve) => {
            this.socket!.emit('unsubscribe_agent_stream', { session_id: sessionId }, (response: any) => {
                this.activeStreams.delete(sessionId);
                this.eventHandlers.delete(sessionId);
                this.historyHandlers.delete(sessionId);

                if (response?.status === 'unsubscribed') {
                    console.log(`[AgentStreamSocket] Unsubscribed from stream ${sessionId}`);
                    resolve();
                } else {
                    // Still resolve since we've cleaned up locally
                    console.warn(`[AgentStreamSocket] Unsubscribe response unexpected:`, response);
                    resolve();
                }
            });
        });
    }

    /**
     * Register a handler for events in a specific agent stream
     * @param sessionId The agent session ID to listen to
     * @param handler Function to handle incoming events
     * @returns Cleanup function to remove the handler
     */
    onStreamEvent(sessionId: string, handler: (event: AgentStreamEvent) => void) {
        if (!this.eventHandlers.has(sessionId)) {
            this.eventHandlers.set(sessionId, new Set());
        }
        this.eventHandlers.get(sessionId)!.add(handler);

        return () => {
            const handlers = this.eventHandlers.get(sessionId);
            if (handlers) {
                handlers.delete(handler);
                if (handlers.size === 0) {
                    this.eventHandlers.delete(sessionId);
                }
            }
        };
    }

    /**
     * Register a handler for history events in a specific agent stream
     * @param sessionId The agent session ID to listen to
     * @param handler Function to handle history events
     * @returns Cleanup function to remove the handler
     */
    onStreamHistory(sessionId: string, handler: (event: AgentStreamHistoryEvent) => void) {
        if (!this.historyHandlers.has(sessionId)) {
            this.historyHandlers.set(sessionId, new Set());
        }
        this.historyHandlers.get(sessionId)!.add(handler);

        return () => {
            const handlers = this.historyHandlers.get(sessionId);
            if (handlers) {
                handlers.delete(handler);
                if (handlers.size === 0) {
                    this.historyHandlers.delete(sessionId);
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
     * Check if currently subscribed to a specific agent stream
     */
    isSubscribed(sessionId: string): boolean {
        return this.activeStreams.has(sessionId);
    }
}

export const agentStreamSocket = new AgentStreamSocketService();
