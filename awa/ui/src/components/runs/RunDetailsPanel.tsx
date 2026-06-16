import { useState } from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import HelpOutlinedIcon from '@mui/icons-material/HelpOutlined';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import TabPanel from '@/components/common/TabPanel';
import RunMetadata from './RunMetadata';
import RunTasksTab from './RunTasksTab';
import AgentStreamingTab from './AgentStreamingTab';
import { useGetWorkflowById } from '@/queries/workflow';
import { navigate } from 'astro:transitions/client';

interface RunDetailsPanelProps {
    runId: string;
}

const RunDetailsPanel = ({ runId }: RunDetailsPanelProps) => {
    const { data: workflow, isLoading } = useGetWorkflowById(runId);
    const [tabValue, setTabValue] = useState(0);

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
        setTabValue(newValue);
    };

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (!workflow) {
        return (
            <Container maxWidth="lg" sx={{ py: 5 }}>
                <Typography variant="h5" color="error">
                    Workflow run not found
                </Typography>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ py: 5 }}>
            <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
                <IconButton onClick={() => navigate('/runs')}>
                    <ArrowBackIcon />
                </IconButton>
                <Typography variant="h4" component="h1" fontWeight="light" gutterBottom>
                    Run Details
                </Typography>
            </Box>

            {/* Top Section - Workflow Metadata */}
            <Paper elevation={3} sx={{ borderRadius: 2, p: 3, mb: 4 }}>
                <RunMetadata workflow={workflow} />
            </Paper>

            {/* Bottom Section - Tabbed Content */}
            <Paper elevation={3} sx={{ borderRadius: 2 }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs value={tabValue} onChange={handleTabChange} aria-label="run details tabs">
                        <Tab label="HITL Tasks" id="tab-0" aria-controls="tabpanel-0" iconPosition="end" icon={
                            <Tooltip title="Human-in-the-loop task: Human input is required to proceed">
                                <HelpOutlinedIcon color="primary" fontSize='small' sx={{ mx: 1 }}/>
                            </Tooltip>
                        }/>
                        <Tab label="Agent Streaming" id="tab-1" aria-controls="tabpanel-1" />
                    </Tabs>
                </Box>
                <TabPanel value={tabValue} index={0}>
                    <RunTasksTab workflowId={runId} />
                </TabPanel>
                <TabPanel value={tabValue} index={1}>
                    <AgentStreamingTab workflowId={workflow.workflowId} />
                </TabPanel>
            </Paper>
        </Container>
    );
}

export default RunDetailsPanel;
