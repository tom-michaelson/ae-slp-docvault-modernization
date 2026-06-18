import { type WorkflowRun } from '@/types';
import { WorkflowStatusBadge } from '@/components/workflows';
import { testId } from '@/utils/constants';
import { TableRow, TableCell, Link } from '@mui/material';
import { navigate } from 'astro:transitions/client';

interface WorkflowListingProps {
    workflow: WorkflowRun,
}

const WorkflowListing = ({ workflow }: WorkflowListingProps) => {
    const handleRowClick = (event: React.MouseEvent) => {
        const url = `/runs/${workflow.id}`;

        // Check for cmd+click (Mac) or ctrl+click (Windows/Linux) or middle-click
        if (event.metaKey || event.ctrlKey || event.button === 1) {
            window.open(url, '_blank');
            event.preventDefault();
        } else {
            navigate(url);
        }
    };

    const getTaskCell = (tasks?: number) => {
        if (!tasks || tasks === 0) {
            return <span className='text-black rounded-full px-3 py-1'>-</span>;
        }
        return <span className='bg-red-200 text-black rounded-full px-3 py-1'>{tasks}</span>
    }

    return (
        <TableRow
            hover
            sx={{ cursor: 'pointer' }}
            data-testid={`${testId.listing.runListing}-${workflow.id}`}
            onClick={handleRowClick}
            onAuxClick={handleRowClick} // For middle-click support
        >
            <TableCell>{workflow.type}</TableCell>
            <TableCell><WorkflowStatusBadge status={workflow.status} /></TableCell>
            <TableCell>{workflow.duration}</TableCell>
            <TableCell>{new Date(workflow.started).toLocaleString()}</TableCell>
            <TableCell>{getTaskCell(workflow.pendingTasksCount)}</TableCell>
        </TableRow>
    );
};

export default WorkflowListing;
