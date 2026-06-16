import MUIProvider from '@/providers/MUIProvider';
import { QueryClient, QueryClientProvider } from 'react-query';
import AuthCookieInitializer from '@/components/AuthCookieInitializer';
import { TasksPanel } from '@/components/tasks';

const TasksPageIsland = () => {
    const queryClient = new QueryClient();
    return (
        <MUIProvider>
            <QueryClientProvider client={queryClient}>
                <AuthCookieInitializer />
                <TasksPanel />
            </QueryClientProvider>
        </MUIProvider>
    );
}

export default TasksPageIsland;
