import { getAvailableWorkflows, getRunningWorkflows, runWorkflow, getWorkflowById } from '@/api/workflow';
import { queryKeys } from '@/lib/queryKeys';
import type { PostResponse, WorkflowInfo, WorkflowRun, WorkflowRunPayload } from '@/types';
import { useMutation, useQuery } from 'react-query';

export const useGetRunningWorkflows = () => {
    return useQuery<WorkflowRun[]>({
        queryKey: queryKeys.workflows.running(),
        queryFn: getRunningWorkflows,
    })
}

export const useGetAvailableWorkflows = () => {
    return useQuery<WorkflowInfo[]>({
        queryKey: queryKeys.workflows.available(),
        queryFn: getAvailableWorkflows,
    })
}

export const useGetWorkflowById = (workflowId: string) => {
    return useQuery<WorkflowRun>({
        queryKey: ['workflow', workflowId],
        queryFn: () => getWorkflowById(workflowId),
        enabled: !!workflowId,
        retry: 1,
        retryDelay: 1000,
    })
}

export const useRunWorkflowMutation = () => {
    return useMutation({
        mutationKey: queryKeys.workflows.run(),
        mutationFn: runWorkflow
    })
}
