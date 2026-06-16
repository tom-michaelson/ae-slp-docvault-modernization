import { getTaskDetails, getTaskList, getTaskListForWorkflow, submitTaskResponse } from '@/api/task';
import { queryKeys } from '@/lib/queryKeys';
import type { HITLTaskInfo, HITLTaskDetail } from '@/types/api_models';
import { useMutation, useQuery } from 'react-query';

export const useGetTaskList = () => {
    return useQuery<HITLTaskInfo[]>({
        queryKey: queryKeys.tasks.list(),
        queryFn: getTaskList,
    })
}
export const useGetTaskDetails = (taskId: string) => {
    return useQuery<HITLTaskDetail>({
        queryKey: queryKeys.tasks.details(taskId),
        queryFn: () => getTaskDetails(taskId),
    })
}

export const useGetTaskListForWorkflow = (workflowId: string) => {
    return useQuery<HITLTaskInfo[]>({
        queryKey: ['tasks', 'workflow', workflowId],
        queryFn: () => getTaskListForWorkflow(workflowId),
        enabled: !!workflowId,
    })
}

export const useTaskSubmissionMutation = (taskId: string) => {
    return useMutation({
        mutationKey: queryKeys.tasks.response(taskId),
        mutationFn: submitTaskResponse
    })
}
