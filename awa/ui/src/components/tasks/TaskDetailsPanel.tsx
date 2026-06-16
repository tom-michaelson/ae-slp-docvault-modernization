import { useState } from 'react';
import {
    Box,
    Container,
    Typography,
    Paper,
    Grid,
    CircularProgress,
    Alert,
    IconButton,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Chip,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useGetTaskDetails } from '../../queries/task';
import { MarkdownRenderer } from '../MarkdownRenderer';
import TaskChatEmbed from './TaskChatEmbed';
import TaskResponseEmbed from './TaskResponseEmbed';
import { navigate } from 'astro:transitions/client';


interface TaskDetailsPanelProps {
    taskId: string;
}

const TaskDetailsPanel = ({ taskId }: TaskDetailsPanelProps) => {
    const { data: task, isLoading, error, refetch } = useGetTaskDetails(taskId);
    const [expanded, setExpanded] = useState<string | false>('metadata');

    const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
        setExpanded(isExpanded ? panel : false);
    };

    const handleCompleted = () => {
        refetch();
        navigate(task ? `/runs/${task.parentRunId}` : '/runs');
    }

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error || !task) {
        return (
            <Container maxWidth="lg" sx={{ py: 5 }}>
                <Alert severity='error'>
                    Failed to load task details. Please try again.
                </Alert>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ py: 5 }}>
            {/* Header with back button and title */}
            <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
                <IconButton onClick={() => navigate(`/runs/${task.parentRunId}`)}>
                    <ArrowBackIcon />
                </IconButton>
                <Typography variant="h4" component="h1" fontWeight="light" gutterBottom>
                    {task.title}
                </Typography>
            </Box>

            {/* Top Section - Task Metadata in Accordion */}
            <Accordion
                expanded={expanded === 'metadata'}
                onChange={handleAccordionChange('metadata')}
            >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Task Metadata</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Grid container spacing={3}>
                        <Grid size={{ xs: 12, sm: 6 }}>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                Task ID
                            </Typography>
                            <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                                {task.id}
                            </Typography>
                        </Grid>

                        <Grid size={{ xs: 12, sm: 6 }}>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                Workflow ID
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                                    {task.workflowId}
                                </Typography>
                            </Box>
                        </Grid>

                        <Grid size={{ xs: 12, sm: 6 }}>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                Start Time
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body1">
                                    {new Date(task.startTime).toLocaleString()}
                                </Typography>
                            </Box>
                        </Grid>

                        {task.description && (
                            <Grid size={{ xs: 12 }}>
                                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                    Description
                                </Typography>
                                <Typography variant="body1">
                                    {task.description}
                                </Typography>
                            </Grid>
                        )}
                    </Grid>
                </AccordionDetails>
            </Accordion>

            {/* Middle Section - Response Details (Markdown) in Accordion */}
            {task.markdown && (
                <Accordion
                    expanded={expanded === 'details'}
                    onChange={handleAccordionChange('details')}
                >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="h6">Response Details</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <Box sx={{ minHeight: 200 }}>
                            <MarkdownRenderer content={task.markdown} />
                        </Box>
                    </AccordionDetails>
                </Accordion>
            )}

            {/* Bottom Section - Response (Chat or Form) */}
            <Paper elevation={3} sx={{ borderRadius: 2, p: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Response
                </Typography>

                {task.chatMode ? (
                    <TaskChatEmbed task={task} onComplete={handleCompleted} />
                ) : (
                    <TaskResponseEmbed task={task} onComplete={handleCompleted} />
                )}
            </Paper>
        </Container>
    );
};

export default TaskDetailsPanel;
