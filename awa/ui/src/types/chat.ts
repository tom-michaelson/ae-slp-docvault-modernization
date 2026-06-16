export interface ChatMessage {
    id: string;
    content: string;
    sender: 'user' | 'agent' | 'system';
    timestamp: Date;
    taskId?: string;
    workflowId?: string;
    status?: 'sending' | 'sent' | 'failed' | 'delivered';
    read?: boolean;
    metadata?: Record<string, any>;
}

export interface ChatState {
    messages: ChatMessage[];
    isOpen: boolean;
    isMinimized: boolean;
    context?: {
        taskId?: string;
        workflowId?: string;
    };
}

export interface ChatSocketEvents {
    'message:send': (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
    'message:receive': (message: ChatMessage) => void;
    'user:join': (userId: string) => void;
    'user:leave': (userId: string) => void;
    'connection': () => void;
    'disconnect': () => void;
}
