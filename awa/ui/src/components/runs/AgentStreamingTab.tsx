import { useRef } from 'react';
import { Box } from '@mui/material';
import AgentWorkflowList, { type AgentWorkflowListRef } from './AgentWorkflowList';

interface AgentStreamingTabProps {
    workflowId: string;
}

const AgentStreamingTab = ({ workflowId }: AgentStreamingTabProps) => {
    const agentListRef = useRef<AgentWorkflowListRef>(null);

    return (
        <Box sx={{ p: 3 }}>
            <AgentWorkflowList workflowId={workflowId} ref={agentListRef} />
        </Box>
    );
};

export default AgentStreamingTab;
