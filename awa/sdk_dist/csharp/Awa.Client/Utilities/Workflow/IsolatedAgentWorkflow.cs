using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;
using Temporalio.Workflows;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Execute an agent in an isolated environment.
        ///
        /// This workflow implements complete separation of concerns:
        /// 1. Environment setup is fully encapsulated in setup activities
        /// 2. Agent execution is completely unaware of environment context
        /// 3. Cleanup and output handling are managed by dedicated activities
        ///
        /// For ACT mode: Uses git worktree for isolated execution and merges changes back
        /// For ANALYZE mode: Uses temporary directory copy for isolated execution and copies outputs back
        /// </summary>
        /// <param name="parameters">Parameters containing source directory, agent config, and options including:
        /// - source_directory: Source directory path (can be Git repo or regular directory)
        /// - source_branch: Source branch name (only used for Git repositories in ACT mode)
        /// - agent_config: Agent configuration for execution
        /// - agent_execution_timeout_minutes: Timeout in minutes for agent execution (default: 10)
        /// - output_directory: Directory name for agent outputs in analyze mode (default: "awa-agent-output")</param>
        /// <param name="workflowId">Optional custom workflow ID. If not provided, will be auto-generated.</param>
        /// <returns>The result of the agent execution with status and details.</returns>
        public static async Task<TaskResponseModel?> IsolatedAgentWorkflow(
            IsolatedAgentParams parameters,
            string? workflowId = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<TaskResponseModel?>(
                AwaConstants.WorkflowIsolatedAgent,
                new object?[] { parameters },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    Id = workflowId ?? $"isolated-agent-{Temporalio.Workflows.Workflow.Info.WorkflowId}"
                });
        }
    }
}
