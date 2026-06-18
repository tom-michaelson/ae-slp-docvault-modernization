using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Add a comment to a Jira issue using the provided request parameters.
        /// </summary>
        /// <param name="request">JiraIssueRequest containing the issue and comment details.</param>
        /// <returns>The result of the comment addition, typically the comment ID.</returns>
        public static async Task<string?> AddJiraCommentActivity(JiraIssueRequest request)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
                AwaConstants.ActivityAddJiraComment,
                new object?[] { request },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.McpTimeoutSeconds)
                });
        }
    }
}
