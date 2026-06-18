using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Read a directory and return detailed information about its contents.
        /// </summary>
        /// <param name="sourcePath">The path to the directory to read.</param>
        /// <param name="ignoreFilePath">Optional path to an ignore file (like .gitignore) to exclude files. Defaults to null.</param>
        /// <returns>A list of ReadDirectoryResult objects containing detailed information about each file and directory.</returns>
        public static async Task<List<ReadDirectoryResult>> ReadDirectoryActivity(
            string sourcePath,
            string? ignoreFilePath = null)
        {
            var rawResults = await Temporalio.Workflows.Workflow.ExecuteActivityAsync<object[]>(
                AwaConstants.ActivityReadDirectory,
                new object?[] { sourcePath, ignoreFilePath },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds * 10)
                });

            return rawResults.Select(result =>
            {
                var dict = result as Dictionary<string, object> ?? new Dictionary<string, object>();
                return new ReadDirectoryResult
                {
                    File = dict.TryGetValue("file", out var file) ? file?.ToString() ?? "" : "",
                    Content = dict.TryGetValue("content", out var content) ? content?.ToString() ?? "" : ""
                };
            }).ToList();
        }
    }
}
