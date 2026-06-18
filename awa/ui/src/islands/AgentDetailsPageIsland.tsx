import MUIProvider from '@/providers/MUIProvider';
import { QueryClient, QueryClientProvider } from 'react-query';
import AuthCookieInitializer from '@/components/AuthCookieInitializer';
import AgentDetailView from '@/components/agent-detail/AgentDetailView';

interface AgentDetailsPageIslandProps {
    workflowId: string;
}

const AgentDetailsPageIsland = ({ workflowId }: AgentDetailsPageIslandProps) => {
    const queryClient = new QueryClient();
    return (
        <MUIProvider>
            <QueryClientProvider client={queryClient}>
                <AuthCookieInitializer />
                <AgentDetailView workflowId={workflowId} />
            </QueryClientProvider>
        </MUIProvider>
    );
}

export default AgentDetailsPageIsland;
