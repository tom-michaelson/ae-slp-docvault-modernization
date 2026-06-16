using System;
using Awa.Client.Models;

namespace Awa.Client.Utilities.General
{
    /// <summary>
    /// General utility functions for AWA SDK.
    /// </summary>
    public static partial class GeneralUtilities
    {
        /// <summary>
        /// Get workflow paths using Temporal workflow info.
        /// </summary>
        /// <param name="workflowDir">The base workflow directory.</param>
        /// <param name="workflowType">Temporal workflow type.</param>
        /// <param name="workflowId">Temporal workflow ID.</param>
        /// <returns>WorkflowPaths object containing all relevant workflow paths.</returns>
        public static WorkflowPaths GetWorkflowPaths(string workflowDir, string workflowType, string workflowId)
        {
            return GetWorkflowPathsDirect(workflowDir, workflowType, workflowId);
        }
    }
}
