/**
 * Shared Socket.IO types for agent streaming events.
 * These match the events emitted by awa/core/api/socketio_server.py
 */

export interface AgentStreamStartEvent {
    session_id: string;
    timestamp: string;
    agent_type?: string;
    status: 'started';
}

export interface AgentStreamOutputEvent {
    session_id: string;
    content: string;
    chunk_index: number;
    is_final: boolean;
    timestamp: string;
    agent_type?: string;
}

export interface AgentStreamCompleteEvent {
    session_id: string;
    timestamp: string;
    final_result?: any;
    execution_time?: number;
    agent_type?: string;
    status: 'completed';
}

export interface AgentStreamErrorEvent {
    session_id: string;
    timestamp: string;
    error: string;
    error_code?: string;
    agent_type?: string;
    status: 'error';
}

export interface AgentStreamHistoryEvent {
    session_id: string;
    history: Array<{
        type: 'start' | 'output' | 'complete' | 'error' | 'message' | 'step';
        [key: string]: any;
    }>;
}

export interface AgentStreamMessageEvent {
    session_id: string;
    message: string;
    data?: Record<string, any>;
    timestamp: string;
}

export interface AgentStreamStepEvent {
    session_id: string;
    step_name: string;
    step_type: 'start' | 'complete' | 'error';
    description?: string;
    result?: string;
    metadata?: Record<string, any>;
    timestamp: string;
}
