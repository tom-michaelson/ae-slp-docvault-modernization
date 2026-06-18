import { useState, useEffect, useCallback } from 'react';
import { useQuery } from 'react-query';
import * as agentStreamingApi from '@/api/agentStreaming';
import { agentStreamSocket, type AgentStreamEvent } from '@/services/agentStreamSocket';
import type {
    AgentStreamStartEvent,
    AgentStreamOutputEvent,
    AgentStreamCompleteEvent,
    AgentStreamErrorEvent,
    AgentStreamMessageEvent,
    AgentStreamStepEvent,
    AgentStreamHistoryEvent,
} from '@/lib/socketio';

/**
 * Hook for querying workflow agent sessions.
 *
 * @param workflowId - The workflow ID to query sessions for
 */
export const useWorkflowAgentSessions = (workflowId: string | undefined) => {
    const { data, isLoading, error, refetch } = useQuery(
        ['workflowAgentSessions', workflowId],
        () => workflowId ? agentStreamingApi.getWorkflowAgentSessions(workflowId) : Promise.resolve(null),
        {
            enabled: !!workflowId,
            refetchOnWindowFocus: false,
        }
    );

    return {
        sessions: data?.sessions || [],
        parentSessionId: data?.parentSessionId || null,
        count: data?.count || 0,
        isLoading,
        error,
        refetch,
    };
};

/**
 * Processed agent stream chunk for display
 */
export interface AgentStreamChunk {
    type: 'start' | 'output' | 'message' | 'step' | 'complete' | 'error';
    timestamp: string;
    content?: string;
    message?: string;
    stepName?: string;
    stepType?: 'start' | 'complete' | 'error';
    description?: string;
    error?: string;
    executionTime?: number;
    agentType?: string;
    metadata?: Record<string, any>;
}

interface UseAgentStreamOptions {
    sessionId: string | null;
    autoConnect?: boolean;
}

interface UseAgentStreamReturn {
    chunks: AgentStreamChunk[];
    fullOutput: string;
    isConnected: boolean;
    isSubscribed: boolean;
    isStreaming: boolean;
    error: string | null;
    clearOutput: () => void;
    subscribeToStream: () => Promise<void>;
    unsubscribeFromStream: () => Promise<void>;
}

/**
 * Hook for subscribing to agent stream real-time events via Socket.IO.
 * Similar to useHitlChat but for agent streaming.
 *
 * @param options - Configuration options
 */
export const useAgentStream = ({
    sessionId,
    autoConnect = true,
}: UseAgentStreamOptions): UseAgentStreamReturn => {
    const [chunks, setChunks] = useState<AgentStreamChunk[]>([]);
    const [fullOutput, setFullOutput] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Process events into chunks
    const processEvent = useCallback((event: AgentStreamEvent): AgentStreamChunk => {
        if ('status' in event && event.status === 'started') {
            const e = event as AgentStreamStartEvent;
            return {
                type: 'start',
                timestamp: e.timestamp,
                agentType: e.agent_type,
            };
        }
        if ('content' in event) {
            const e = event as AgentStreamOutputEvent;
            return {
                type: 'output',
                timestamp: e.timestamp,
                content: e.content,
                agentType: e.agent_type,
            };
        }
        if ('step_name' in event) {
            const e = event as AgentStreamStepEvent;
            return {
                type: 'step',
                timestamp: e.timestamp,
                stepName: e.step_name,
                stepType: e.step_type,
                description: e.description,
                metadata: e.metadata,
            };
        }
        if ('message' in event && !('error' in event)) {
            const e = event as AgentStreamMessageEvent;
            return {
                type: 'message',
                timestamp: e.timestamp,
                message: e.message,
                metadata: e.data,
            };
        }
        if ('status' in event && event.status === 'completed') {
            const e = event as AgentStreamCompleteEvent;
            return {
                type: 'complete',
                timestamp: e.timestamp,
                executionTime: e.execution_time,
                agentType: e.agent_type,
            };
        }
        if ('error' in event) {
            const e = event as AgentStreamErrorEvent;
            return {
                type: 'error',
                timestamp: e.timestamp,
                error: e.error,
                agentType: e.agent_type,
            };
        }
        // Fallback
        return {
            type: 'message',
            timestamp: new Date().toISOString(),
            message: JSON.stringify(event),
        };
    }, []);

    // Build full output from chunks
    useEffect(() => {
        const outputParts: string[] = [];

        for (const chunk of chunks) {
            if (chunk.type === 'output' && chunk.content) {
                outputParts.push(chunk.content);
            } else if (chunk.type === 'message' && chunk.message) {
                outputParts.push(`\n[${new Date(chunk.timestamp).toLocaleTimeString()}] ${chunk.message}\n`);
            } else if (chunk.type === 'step') {
                const stepLabel = chunk.stepType === 'start' ? '→' : chunk.stepType === 'complete' ? '✓' : '✗';
                outputParts.push(`\n[${stepLabel}] ${chunk.stepName}${chunk.description ? ': ' + chunk.description : ''}\n`);
            } else if (chunk.type === 'error' && chunk.error) {
                outputParts.push(`\n[ERROR] ${chunk.error}\n`);
            } else if (chunk.type === 'complete') {
                outputParts.push(`\n[✓] Completed${chunk.executionTime ? ` in ${chunk.executionTime.toFixed(2)}s` : ''}\n`);
            }
        }

        setFullOutput(outputParts.join(''));
    }, [chunks]);

    // Subscribe to stream
    const subscribeToStream = useCallback(async () => {
        if (!sessionId) return;
        if (!agentStreamSocket.isConnected()) {
            throw new Error('Socket not connected');
        }

        try {
            await agentStreamSocket.subscribeToAgentStream(sessionId);
            setIsSubscribed(true);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to subscribe');
            setIsSubscribed(false);
            throw err;
        }
    }, [sessionId]);

    // Unsubscribe from stream
    const unsubscribeFromStream = useCallback(async () => {
        if (!sessionId) return;

        try {
            await agentStreamSocket.unsubscribeFromAgentStream(sessionId);
            setIsSubscribed(false);
        } catch (err) {
            console.error('[useAgentStream] Failed to unsubscribe:', err);
            setIsSubscribed(false);
        }
    }, [sessionId]);

    // Clear output
    const clearOutput = useCallback(() => {
        setChunks([]);
        setFullOutput('');
    }, []);

    // Handle WebSocket connection and subscription
    useEffect(() => {
        if (!autoConnect || !sessionId) {
            console.log('[useAgentStream] Not auto-connecting:', { autoConnect, sessionId });
            return;
        }

        console.log('[useAgentStream] Setting up connection for session:', sessionId);

        // Connect to socket
        agentStreamSocket.connect();

        // Track connection status
        const unsubscribeConnection = agentStreamSocket.onConnectionChange((connected) => {
            console.log('[useAgentStream] Connection changed:', connected);
            setIsConnected(connected);

            // Auto-subscribe on connection (not just reconnection)
            if (connected && !agentStreamSocket.isSubscribed(sessionId)) {
                console.log('[useAgentStream] Connected, attempting to subscribe');
                subscribeToStream().catch(err => {
                    console.error('[useAgentStream] Auto-subscribe failed:', err);
                });
            }
        });

        // Set initial connection state
        const initiallyConnected = agentStreamSocket.isConnected();
        console.log('[useAgentStream] Initially connected:', initiallyConnected);
        setIsConnected(initiallyConnected);

        // Handle incoming events
        const unsubscribeEvents = agentStreamSocket.onStreamEvent(sessionId, (event: AgentStreamEvent) => {
            console.log('[useAgentStream] Received event:', event);
            const chunk = processEvent(event);
            setChunks(prev => [...prev, chunk]);

            // Update streaming state
            if (chunk.type === 'start') {
                setIsStreaming(true);
            } else if (chunk.type === 'complete' || chunk.type === 'error') {
                setIsStreaming(false);
            }
        });

        // Handle history events (for late subscribers)
        const unsubscribeHistory = agentStreamSocket.onStreamHistory(sessionId, (historyEvent: AgentStreamHistoryEvent) => {
            console.log('[useAgentStream] Received history:', historyEvent);
            const historyChunks = historyEvent.history.map(item => {
                // Convert history item to AgentStreamEvent format
                return processEvent(item as any);
            });
            setChunks(historyChunks);
        });

        // Auto-subscribe if already connected
        if (initiallyConnected && !agentStreamSocket.isSubscribed(sessionId)) {
            console.log('[useAgentStream] Already connected, subscribing immediately');
            subscribeToStream().catch(err => {
                console.error('[useAgentStream] Immediate subscribe failed:', err);
            });
        }

        return () => {
            unsubscribeConnection();
            unsubscribeEvents();
            unsubscribeHistory();
        };
    }, [sessionId, autoConnect, subscribeToStream, processEvent]);

    return {
        chunks,
        fullOutput,
        isConnected,
        isSubscribed,
        isStreaming,
        error,
        clearOutput,
        subscribeToStream,
        unsubscribeFromStream,
    };
};
