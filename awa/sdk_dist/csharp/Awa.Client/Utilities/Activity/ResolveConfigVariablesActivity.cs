using System;
using System.Threading.Tasks;
using Temporalio.Workflows;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    /// <summary>
    /// Activity utilities for AWA SDK.
    /// </summary>
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Resolves environment variable placeholders in configuration objects.
        /// Recursively expands environment variable placeholders in nested objects.
        /// Handles ${VAR_NAME} and $VAR patterns in strings within nested dictionaries/lists.
        /// Raises an error if any required environment variables are not found.
        /// </summary>
        /// <param name="configObject">The configuration object to process. Can be a dictionary, list, string, or any other type.</param>
        /// <returns>The configuration object with environment variable placeholders expanded.</returns>
        /// <exception cref="ArgumentException">Thrown if required environment variables are not set.</exception>
        public static async Task<object?> ResolveConfigVariablesActivity(object? configObject)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<object?>(
                AwaConstants.ActivityResolveConfigVariables,
                new object?[] { configObject },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
