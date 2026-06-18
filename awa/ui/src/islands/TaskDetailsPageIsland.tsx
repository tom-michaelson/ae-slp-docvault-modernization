import MUIProvider from '@/providers/MUIProvider';
import { QueryClient, QueryClientProvider } from 'react-query';
import AuthCookieInitializer from '@/components/AuthCookieInitializer';
import { TaskDetailsPanel } from '@/components/tasks';

interface TaskDetailsPageIslandProps {
    taskId: string;
}

const TaskDetailsPageIsland = ({ taskId }: TaskDetailsPageIslandProps) => {
    const queryClient = new QueryClient();
    return (
        <MUIProvider>
            <QueryClientProvider client={queryClient}>
                <AuthCookieInitializer />
                <TaskDetailsPanel taskId={taskId} />
            </QueryClientProvider>
        </MUIProvider>
    );
}

export default TaskDetailsPageIsland;
