import { useState } from 'react';
import {
    Box,
    Container,
    Typography,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    CircularProgress,
    Tooltip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { WorkflowsModal, WorkflowListing } from '@/components/workflows';
import { useGetRunningWorkflows } from '@/queries/workflow';
import { testId } from '@/utils/constants';
import HelpOutlinedIcon from '@mui/icons-material/HelpOutlined';

const WorkflowsPanel = () => {
    const { data: workflows, refetch, isLoading } = useGetRunningWorkflows();
    const [open, setOpen] = useState(false);

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ py: 5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Typography variant="h3" component="h1" fontWeight="light">
                    Workflow Runs
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpen(true)}
                    data-testid={testId.panel.newRunButton}
                    sx={{ py: 1, px: 3 }}
                >
                    New Run
                </Button>
            </Box>

            <Paper elevation={3} sx={{ borderRadius: 2 }}>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Workflow</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Duration</TableCell>
                                <TableCell>Started</TableCell>
                                <TableCell>
                                    HITL Tasks
                                    <Tooltip title="Human-in-the-loop task: Human input is required to proceed">
                                        <HelpOutlinedIcon color="primary" fontSize='small' sx={{ mx: 1 }}/>
                                    </Tooltip>
                                </TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {workflows?.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} align="center" sx={{ py: 5 }}>
                                        <Typography variant="body1" color="text.secondary">
                                            No Runs
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                workflows?.map((workflow) => (
                                    <WorkflowListing workflow={workflow} key={workflow.id} />
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>

            <WorkflowsModal open={open} onClose={() => {
                setOpen(false);
                refetch();

                // Delayed refetch after 3 seconds
                setTimeout(() => {
                    refetch();
                }, 3000);

            }} />
        </Container>
    );
}

export default WorkflowsPanel;
