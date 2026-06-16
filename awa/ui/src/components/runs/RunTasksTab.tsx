import {
    Box,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    CircularProgress,
} from '@mui/material';
import { TaskListing } from '@/components/tasks';
import { useGetTaskListForWorkflow } from '@/queries/task';
import type { HITLTaskInfo } from '@/types';

interface RunTasksTabProps {
    workflowId: string;
}

const RunTasksTab = ({ workflowId }: RunTasksTabProps) => {
    const { data: workflowTasks, isLoading } = useGetTaskListForWorkflow(workflowId);

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ px: 2 }}>
            <TableContainer>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Title</TableCell>
                            <TableCell>Description</TableCell>
                            <TableCell>Task ID</TableCell>
                            <TableCell>Started</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {!workflowTasks || workflowTasks.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} align="center" sx={{ py: 5 }}>
                                    <Typography variant="body1" color="text.secondary">
                                        No tasks for this workflow
                                    </Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            workflowTasks.map((task: HITLTaskInfo) => (
                                <TaskListing task={task} key={task.id} />
                            ))
                        )}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}

export default RunTasksTab;
