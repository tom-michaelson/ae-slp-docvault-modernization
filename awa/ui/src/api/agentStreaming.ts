import api from '@/lib/api';
import type { WorkflowAgentSessionsResponse, AgentSession } from '@/types/api_models';

/**
 * Get all agent streaming sessions for a workflow.
 * Works with any workflow that inherits from AgentSessionTrackingMixin.
 */
export const getWorkflowAgentSessions = async (workflowId: string): Promise<WorkflowAgentSessionsResponse> => {
    const { data } = await api.get(`/api/v1/workflows/${workflowId}/agent-sessions`);
    return {
        workflowId: data.workflow_id,
        sessions: data.sessions?.map((item: any): AgentSession => ({
            sessionId: item.session_id,
            sessionType: item.session_type,
        })) || [],
        count: data.count || 0,
    };
}
