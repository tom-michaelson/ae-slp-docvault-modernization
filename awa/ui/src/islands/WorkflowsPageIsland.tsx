import MUIProvider from '@/providers/MUIProvider';
import { QueryClient, QueryClientProvider } from 'react-query';
import { WorkflowsPanel } from '@/components/workflows';
import AuthCookieInitializer from '@/components/AuthCookieInitializer';

const WorkflowsPageIsland = () => {
    const queryClient = new QueryClient();
    return (
        <MUIProvider>
            <QueryClientProvider client={queryClient}>
                <AuthCookieInitializer />
                <WorkflowsPanel />
            </QueryClientProvider>
        </MUIProvider>
    );
}

export default WorkflowsPageIsland;
