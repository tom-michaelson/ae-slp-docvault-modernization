import { useState, useEffect } from 'react';
import { Container, Paper, Alert, Box, Chip, Typography, Button } from '@mui/material';
import { useWorkflowAgentSessions, useAgentStream } from '@/hooks/useAgentStreaming';
import AgentDetailHeader from './AgentDetailHeader';
import AgentConnectionStatus from './AgentConnectionStatus';
import AgentOutputSection from './AgentOutputSection';
import AgentSessionDetails from './AgentSessionDetails';

interface AgentDetailViewProps {
    workflowId: string; // Actually a session ID (due to route naming)
}

/**
 * Agent Detail View Component
 *
 * Displays real-time agent streaming output for a specific session using Socket.IO.
 * Extracts the workflow ID from the session ID to query for all sessions,
 * then subscribes to the specific session for real-time streaming updates.
 */
const AgentDetailView = ({ workflowId: sessionId }: AgentDetailViewProps) => {
    // Extract workflow ID from session ID
    // Pattern: {prefix}-{workflow_id}-{suffix}
    const extractWorkflowId = (sessionId: string): string => {
        // Use regex to find the workflow ID pattern: YYYYMMDD_HHMMSS_MS_HASH
        const match = sessionId.match(/(\d{8}_\d{6}_\d+_[a-f0-9]+)/);
        if (match) {
            return match[1];
        }
        // Fallback: assume it's already a workflow ID
        return sessionId;
    };

    const workflowId = extractWorkflowId(sessionId);

    // Load agent sessions for this workflow
    const { sessions, parentSessionId, isLoading: loadingSessions, error: sessionsError, refetch } = useWorkflowAgentSessions(workflowId);

    // Connect to Socket.IO stream using the specific session ID (not parent)
    const {
        fullOutput,
        isConnected,
        isSubscribed,
        isStreaming,
        error: streamError,
        chunks,
    } = useAgentStream({
        sessionId: sessionId, // Subscribe to the specific session, not the parent
        autoConnect: true,
    });

    // Combined loading and error states
    const isLoading = loadingSessions;
    const error = sessionsError || streamError;

    // Find the specific session we're viewing
    const currentSession = sessions.find(s => s.sessionId === sessionId);

    // Determine connection status
    const getConnectionStatus = () => {
        if (isLoading) return 'connecting';
        if (!isConnected) return 'disconnected';
        if (!isSubscribed) return 'connecting';
        if (isStreaming) return 'streaming';
        return 'ready';
    };

    return (
        <Container maxWidth="lg" sx={{ py: 5 }}>
            <AgentDetailHeader workflowId={sessionId} />

            <Paper elevation={3} sx={{ borderRadius: 2, p: 3 }}>
                {/* Connection info banner */}
                {currentSession && (
                    <Box sx={{ mb: 3 }}>
                        <Alert
                            severity={isConnected && isSubscribed ? 'success' : 'info'}
                            icon={false}
                        >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                                <Box>
                                    <strong>Session:</strong> {sessionId}
                                </Box>
                                <Chip
                                    label={currentSession.sessionType}
                                    color="primary"
                                    size="small"
                                />
                                <Chip
                                    label={isConnected ? 'Connected' : 'Disconnected'}
                                    color={isConnected ? 'success' : 'default'}
                                    size="small"
                                />
                                <Chip
                                    label={isSubscribed ? 'Subscribed' : 'Not Subscribed'}
                                    color={isSubscribed ? 'success' : 'default'}
                                    size="small"
                                />
                            </Box>
                        </Alert>
                    </Box>
                )}

                {/* Show message if session not found */}
                {!currentSession && !isLoading && (
                    <Box sx={{ mb: 3, textAlign: 'center', py: 4 }}>
                        <Typography variant="h6" gutterBottom>
                            Session Not Found
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            The session <code>{sessionId}</code> could not be found.
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={() => window.history.back()}
                        >
                            Back to Workflow Details
                        </Button>
                    </Box>
                )}

                {/* Only show streaming UI if session exists */}
                {currentSession && (
                    <>
                        <AgentConnectionStatus
                            isConnected={isConnected && isSubscribed}
                            status={getConnectionStatus()}
                            sessionId={sessionId}
                        />

                        <AgentOutputSection
                            output={fullOutput || (chunks.length === 0 ? 'Waiting for agent output...' : '')}
                            status={isStreaming ? 'streaming' : 'completed'}
                            error={error ? String(error) : undefined}
                            isActive={isStreaming}
                            onClearError={() => {}}
                        />

                        <AgentSessionDetails
                            sessionStatus={{
                                sessionId: sessionId,
                                status: getConnectionStatus(),
                                workflowId: workflowId,
                                isActive: isStreaming,
                                messageCount: chunks.length,
                            }}
                            onRefresh={refetch}
                        />
                    </>
                )}
            </Paper>
        </Container>
    );
};

export default AgentDetailView;
