import api from '@/lib/api';
import type { HITLTaskDetail, HITLTaskInfo, HITLChatMessage, PostResponse } from '@/types/api_models';

export const getTaskList = async (): Promise<HITLTaskInfo[]> => {
    const { data } = await api.get('/api/v1/hitl/tasks');
    return data.map((task: any) => ({
        chatMode: task.chat_mode,
        description: task.description,
        id: task.id,
        nonBlocking: task.non_blocking,
        startTime: task.start_time,
        title: task.title,
        workflowId: task.workflow_id,
    }));
}

export const getTaskDetails = async (taskId: string): Promise<HITLTaskDetail> => {
    const { data } = await api.get(`/api/v1/hitl/task/${taskId}`);
    return {
        attachments: data.attachment,
        chatHistory: data.chat_history,
        chatMode: data.chat_mode,
        description: data.description,
        id: data.id,
        inputSchema: data.input_schema,
        markdown: data.markdown,
        parentRunId: data.parent_run_id,
        responseReceived: data.response_received,
        startTime: data.start_time,
        timedOut: data.timed_out,
        title: data.title,
        workflowId: data.workflow_id,
    };
}

export const submitTaskResponse = async ({ taskId, input }: { taskId: string, input: any }): Promise<PostResponse> => {
    const { data: { data } } = await api.post(`/api/v1/hitl/task/${taskId}/submit`, input);
    return data;
}

export const getChatHistory = async (taskId: string): Promise<HITLChatMessage[]> => {
    const { data } = await api.get(`/api/v1/hitl/task/${taskId}/chat/history`);
    return data.map((msg: any) => ({
        message: msg.message,
        timestamp: msg.timestamp ? new Date(msg.timestamp) : undefined,
        isHuman: msg.isHuman,
        data: msg.data,
    }));
}

export const sendUserMessage = async (taskId: string, message: string, userInfo?: Record<string, any>): Promise<void> => {
    await api.post(`/api/v1/hitl/task/${taskId}/chat/user-message`, {
        message,
        user_info: userInfo || {},
    });
}

export const getTaskListForWorkflow = async (workflowId: string): Promise<HITLTaskInfo[]> => {
    const { data } = await api.get(`/api/v1/hitl/tasks/${workflowId}`);
    return data.map((task: any) => ({
        chatMode: task.chat_mode,
        description: task.description,
        id: task.id,
        nonBlocking: task.non_blocking,
        startTime: task.start_time,
        title: task.title,
        workflowId: task.workflow_id,
    }));
}
