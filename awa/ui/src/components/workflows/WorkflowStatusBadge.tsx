import { WorkflowRunStatus } from "@/types";
import { testId } from "@/utils/constants";

interface WorkflowStatusBadgeProps {
    status: WorkflowRunStatus
}

const WorkflowStatusBadge = ({ status }: WorkflowStatusBadgeProps) => {
    return <span
        data-testid={testId.statusBadge.badge}
        className={
        status === WorkflowRunStatus.Canceled ? 'bg-slate-100 text-black rounded-full px-3 py-1' :
        status === WorkflowRunStatus.Completed ? 'bg-green-200 text-black rounded-full px-3 py-1' :
        status === WorkflowRunStatus.ContinuedAsNew ? 'bg-purple-200 text-black rounded-full px-3 py-1' :
        status === WorkflowRunStatus.Failed ? 'bg-red-200 text-black rounded-full px-3 py-1' :
        status === WorkflowRunStatus.Running ? 'bg-blue-300 text-black rounded-full px-3 py-1' :
        status === WorkflowRunStatus.Terminated ? 'bg-yellow-200 text-black rounded-full px-3 py-1' :
        status === WorkflowRunStatus.TimedOut ? 'bg-orange-200 text-black rounded-full px-3 py-1' :
        status === WorkflowRunStatus.Unknown ? 'bg-neutral-600 text-white rounded-full px-3 py-1' :
        status === WorkflowRunStatus.Unspecified ? 'bg-slate-100 text-black rounded-full px-3 py-1' :
        'bg-gray-300 text-white rounded-full px-3 py-1'
    }>{status}</span>
}

export default WorkflowStatusBadge;
