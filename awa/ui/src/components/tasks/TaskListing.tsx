import type { HITLTaskInfo } from '@/types';
import { testId } from '@/utils/constants';
import { navigate } from 'astro:transitions/client';
import { TableRow, TableCell } from '@mui/material';

interface TaskListingProps {
    task: HITLTaskInfo,
}

const TaskListing = ({ task }: TaskListingProps) => {
    const handleRowClick = (e: React.MouseEvent) => {
        // Middle click (button 1) or Cmd/Ctrl + click - open in new tab
        if (e.button === 1 || e.metaKey || e.ctrlKey) {
            window.open(`/tasks/${task.id}`, '_blank');
        } else {
            navigate(`/tasks/${task.id}`);
        }
    };

    return (
        <TableRow
            hover
            sx={{ cursor: 'pointer' }}
            data-testid={`${testId.tasks.taskListing}-${task.id}`}
            onClick={handleRowClick}
            onAuxClick={handleRowClick}
        >
            <TableCell>{task.title}</TableCell>
            <TableCell>{task.description}</TableCell>
            <TableCell>{task.id}</TableCell>
            <TableCell>{new Date(task.startTime).toLocaleString()}</TableCell>
        </TableRow>
    );
};

export default TaskListing;
