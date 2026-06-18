using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Read a Jira issue using the provided request parameters.
        /// </summary>
        /// <param name="request">JiraIssueRequest containing the issue details to read.</param>
        /// <returns>The response containing the Jira issue information.</returns>
        public static async Task<JiraIssueResponse?> ReadJiraIssueActivity(JiraIssueRequest request)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<JiraIssueResponse?>(
                AwaConstants.ActivityReadJiraIssue,
                new object?[] { request },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.McpTimeoutSeconds)
                });
        }
    }
}
