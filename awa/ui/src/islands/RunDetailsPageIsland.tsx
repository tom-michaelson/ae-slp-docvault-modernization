import MUIProvider from '@/providers/MUIProvider';
import { QueryClient, QueryClientProvider } from 'react-query';
import AuthCookieInitializer from '@/components/AuthCookieInitializer';
import RunDetailsPanel from '@/components/runs/RunDetailsPanel';

interface RunDetailsPageIslandProps {
    runId: string;
}

const RunDetailsPageIsland = ({ runId }: RunDetailsPageIslandProps) => {
    const queryClient = new QueryClient();
    return (
        <MUIProvider>
            <QueryClientProvider client={queryClient}>
                <AuthCookieInitializer />
                <RunDetailsPanel runId={runId} />
            </QueryClientProvider>
        </MUIProvider>
    );
}

export default RunDetailsPageIsland;
