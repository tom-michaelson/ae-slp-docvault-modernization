using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Create or update a Jira issue using the provided request parameters.
        /// </summary>
        /// <param name="request">JiraIssueRequest containing the issue details to create or update.</param>
        /// <returns>The result of the upsert operation, typically the issue key or ID.</returns>
        public static async Task<string?> UpsertJiraIssueActivity(JiraIssueRequest request)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
                AwaConstants.ActivityUpsertJiraIssue,
                new object?[] { request },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.McpTimeoutSeconds)
                });
        }
    }
}
