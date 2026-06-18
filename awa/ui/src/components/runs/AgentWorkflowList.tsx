import React, { useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import {
    Box,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    CircularProgress,
    Alert,
    IconButton,
    Tooltip,
    Button,
} from '@mui/material';
import {
    Refresh,
    PlayArrow,
    OpenInNew,
} from '@mui/icons-material';
import { navigate } from 'astro:transitions/client';
import * as agentStreamingApi from '@/api/agentStreaming';
import type { AgentSession } from '@/types/api_models';

interface AgentWorkflowListProps {
    workflowId: string;
}

export interface AgentWorkflowListRef {
    refresh: () => void;
}

const AgentWorkflowList = forwardRef<AgentWorkflowListRef, AgentWorkflowListProps>(({ workflowId }, ref) => {
    const [sessions, setSessions] = useState<AgentSession[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAgentSessions = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await agentStreamingApi.getWorkflowAgentSessions(workflowId);
            setSessions(data.sessions);
        } catch (err) {
            console.error('Failed to fetch agent sessions:', err);
            setError('Failed to load agent sessions. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // Expose refresh method to parent component
    useImperativeHandle(ref, () => ({
        refresh: fetchAgentSessions,
    }));

    useEffect(() => {
        fetchAgentSessions();
    }, [workflowId]);

    const handleRowClick = (sessionId: string, e?: React.MouseEvent) => {
        // Middle click (button 1) or Cmd/Ctrl + click - open in new tab
        if (e && (e.button === 1 || e.metaKey || e.ctrlKey)) {
            window.open(`/agents/${sessionId}`, '_blank');
        } else {
            // Navigate to full agent detail page for this session
            navigate(`/agents/${sessionId}`);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ m: 3 }}>
                {error}
                <Button onClick={fetchAgentSessions} sx={{ ml: 2 }}>
                    Retry
                </Button>
            </Alert>
        );
    }

    if (sessions.length === 0) {
        return (
            <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body1" color="text.secondary">
                    No agent sessions found for this workflow.
                </Typography>
                <Button
                    startIcon={<Refresh />}
                    onClick={fetchAgentSessions}
                    sx={{ mt: 2 }}
                >
                    Refresh
                </Button>
            </Box>
        );
    }

    return (
        <Box>
            {/* Agents List Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                    Agent Sessions ({sessions.length})
                </Typography>
                <Tooltip title="Refresh agent sessions">
                    <IconButton onClick={fetchAgentSessions} size="small">
                        <Refresh />
                    </IconButton>
                </Tooltip>
            </Box>

            <TableContainer component={Paper} elevation={0}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Session ID</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell align="center">Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {sessions.map((session) => (
                            <TableRow
                                key={session.sessionId}
                                hover
                                sx={{ cursor: 'pointer' }}
                                onClick={(e) => handleRowClick(session.sessionId, e)}
                                onAuxClick={(e) => handleRowClick(session.sessionId, e)}
                            >
                                <TableCell>
                                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                        {session.sessionId}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Chip
                                        label={session.sessionType}
                                        color="primary"
                                        size="small"
                                    />
                                </TableCell>
                                <TableCell align="center">
                                    <Tooltip title="View agent streaming output">
                                        <IconButton
                                            size="small"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleRowClick(session.sessionId, e);
                                            }}
                                            onAuxClick={(e) => {
                                                e.stopPropagation();
                                                handleRowClick(session.sessionId, e);
                                            }}
                                        >
                                            <OpenInNew fontSize="small" />
                                        </IconButton>
                                    </Tooltip>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
});

export default AgentWorkflowList;
