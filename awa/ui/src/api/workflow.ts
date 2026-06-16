import api from '@/lib/api';
import type { WorkflowRun, WorkflowInfo, PostResponse, WorkflowRunPayload } from '@/types';

export const getRunningWorkflows = async (): Promise<WorkflowRun[]> => {
    const { data: { workflows } } = await api.get('/api/v1/workflows/runs');
    return workflows.map((workflow: any) => ({
        duration: workflow.duration,
        id: workflow.id,
        workflowId: workflow.workflow_id,
        monitor: workflow.monitor,
        pendingTasksCount: workflow.pending_tasks_count,
        started: workflow.started,
        status: workflow.status,
        type: workflow.type,
    }));
}

export const getAvailableWorkflows = async (): Promise<WorkflowInfo[]> => {
    const { data: { workflows } } = await api.get('/api/v1/workflows/list');
    return workflows;
}

export const runWorkflow = async (payload: WorkflowRunPayload): Promise<PostResponse> => {
    const { data: { data } } = await api.post('/api/v1/workflows', payload);
    return data;
}

export const getWorkflowById = async (workflowId: string): Promise<WorkflowRun> => {
    const { data } = await api.get(`/api/v1/workflows/runs/${workflowId}`);
    return {
        duration: data.duration,
        id: data.id,
        workflowId: data.workflow_id,
        monitor: data.monitor,
        pendingTasksCount: data.pending_tasks_count,
        started: data.started,
        status: data.status,
        type: data.type,
    };
}
