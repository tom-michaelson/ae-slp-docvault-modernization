import { Box, Typography, Link, Grid } from '@mui/material';
import { WorkflowStatusBadge } from '@/components/workflows';
import type { WorkflowRun } from '@/types';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

interface RunMetadataProps {
    workflow: WorkflowRun;
}

const RunMetadata = ({ workflow }: RunMetadataProps) => {
    return (
        <Box>
            <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Run ID
                    </Typography>
                    <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                        {workflow.id}
                    </Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Workflow ID
                    </Typography>
                    <Typography variant="body1">
                        {workflow.workflowId}
                    </Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Workflow Type
                    </Typography>
                    <Typography variant="body1">
                        {workflow.type}
                    </Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Status
                    </Typography>
                    <WorkflowStatusBadge status={workflow.status} />
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Started Time
                    </Typography>
                    <Typography variant="body1">
                        {new Date(workflow.started).toLocaleString()}
                    </Typography>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Duration
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AccessTimeIcon fontSize="small" color="action" />
                        <Typography variant="body1">
                            {workflow.duration}
                        </Typography>
                    </Box>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Temporal UI
                    </Typography>
                    <Link
                        href={workflow.monitor}
                        target="_blank"
                        rel="noopener noreferrer"
                        underline="hover"
                    >
                        View in Temporal
                    </Link>
                </Grid>
            </Grid>
        </Box>
    );
}

export default RunMetadata;
