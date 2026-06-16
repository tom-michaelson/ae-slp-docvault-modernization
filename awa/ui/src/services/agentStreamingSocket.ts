import { io, Socket } from 'socket.io-client';

export interface AgentStreamData {
    session_id: string;
    content: string;
    chunk_index: number;
    is_final: boolean;
    timestamp: string;
}

export interface AgentStreamComplete {
    session_id: string;
    total_chunks: number;
    final_output: string;
    execution_time: number;
}

export interface AgentStreamError {
    session_id: string;
    error_message: string;
    error_type: string;
}

class AgentStreamingSocketService {
    private socket: Socket | null = null;
    private outputHandlers: Map<string, (data: AgentStreamData) => void> = new Map();
    private completeHandlers: Map<string, (data: AgentStreamComplete) => void> = new Map();
    private errorHandlers: Map<string, (error: AgentStreamError) => void> = new Map();
    private connectionHandlers: Set<(connected: boolean) => void> = new Set();

    connect(url?: string) {
        if (this.socket?.connected) {
            return;
        }

        const socketUrl = url || import.meta.env.PUBLIC_SOCKET_URL || 'http://localhost:8001';

        this.socket = io(socketUrl, {
            path: '/ws/socket.io/',
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });

        this.socket.on('connect', () => {
            console.log('Agent streaming socket connected');
            this.connectionHandlers.forEach(handler => handler(true));
        });

        this.socket.on('disconnect', () => {
            console.log('Agent streaming socket disconnected');
            this.connectionHandlers.forEach(handler => handler(false));
        });

        // Handle streaming output chunks
        this.socket.on('agent_stream_output', (data: AgentStreamData) => {
            console.log('Received agent stream output:', data);
            const handler = this.outputHandlers.get(data.session_id);
            if (handler) {
                handler(data);
            }
        });

        // Handle stream completion
        this.socket.on('agent_stream_complete', (data: AgentStreamComplete) => {
            console.log('Agent stream completed:', data);
            const handler = this.completeHandlers.get(data.session_id);
            if (handler) {
                handler(data);
            }
        });

        // Handle stream errors
        this.socket.on('agent_stream_error', (error: AgentStreamError) => {
            console.error('Agent stream error:', error);
            const handler = this.errorHandlers.get(error.session_id);
            if (handler) {
                handler(error);
            }
        });
    }

    disconnect() {
        this.socket?.disconnect();
        this.socket = null;
        this.outputHandlers.clear();
        this.completeHandlers.clear();
        this.errorHandlers.clear();
    }

    // Subscribe to agent stream by session_id
    subscribeToStream(sessionId: string) {
        if (!this.socket?.connected) {
            console.error('Socket not connected');
            return;
        }

        console.log('Subscribing to agent stream:', sessionId);
        this.socket.emit('subscribe_agent_stream', { session_id: sessionId });
    }

    // Unsubscribe from agent stream
    unsubscribeFromStream(sessionId: string) {
        if (!this.socket?.connected) {
            return;
        }

        console.log('Unsubscribing from agent stream:', sessionId);
        this.socket.emit('unsubscribe_agent_stream', { session_id: sessionId });

        // Clean up handlers for this session
        this.outputHandlers.delete(sessionId);
        this.completeHandlers.delete(sessionId);
        this.errorHandlers.delete(sessionId);
    }

    // Register handler for streaming output
    onStreamOutput(sessionId: string, handler: (data: AgentStreamData) => void) {
        this.outputHandlers.set(sessionId, handler);
        return () => this.outputHandlers.delete(sessionId);
    }

    // Register handler for stream completion
    onStreamComplete(sessionId: string, handler: (data: AgentStreamComplete) => void) {
        this.completeHandlers.set(sessionId, handler);
        return () => this.completeHandlers.delete(sessionId);
    }

    // Register handler for stream errors
    onStreamError(sessionId: string, handler: (error: AgentStreamError) => void) {
        this.errorHandlers.set(sessionId, handler);
        return () => this.errorHandlers.delete(sessionId);
    }

    // Register handler for connection changes
    onConnectionChange(handler: (connected: boolean) => void) {
        this.connectionHandlers.add(handler);
        return () => this.connectionHandlers.delete(handler);
    }

    isConnected(): boolean {
        return this.socket?.connected ?? false;
    }
}

export const agentStreamingSocket = new AgentStreamingSocketService();
