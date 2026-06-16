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
    CircularProgress,
} from '@mui/material';
import { TaskListing } from '@/components/tasks';
import { useGetTaskList } from '@/queries/task';
import type { HITLTaskInfo } from '@/types';

const TasksPanel = () => {
    const { data: tasks, isLoading } = useGetTaskList();

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ py: 5 }}>
            <Box sx={{ mb: 4 }}>
                <Typography variant="h3" component="h1" fontWeight="light" gutterBottom>
                    Workflow Tasks
                </Typography>
            </Box>

            <Paper elevation={3} sx={{ borderRadius: 2 }}>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Title</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Workflow ID</TableCell>
                                <TableCell>Started</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {!tasks || tasks?.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={4} align="center" sx={{ py: 5 }}>
                                        <Typography variant="body1" color="text.secondary">
                                            No Tasks
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                tasks?.map((task: HITLTaskInfo) => (
                                    <TaskListing task={task} key={task.id} />
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </Container>
    );
}

export default TasksPanel;
