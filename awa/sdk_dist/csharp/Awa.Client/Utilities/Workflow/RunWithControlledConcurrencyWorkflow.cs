using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Run a list of async functions with controlled concurrency.
        /// </summary>
        /// <param name="asyncFunctions">List of async functions to execute</param>
        /// <param name="maxConcurrency">Maximum number of functions to run simultaneously</param>
        /// <returns>List of results in the same order as the input async functions</returns>
        public static async Task<List<object?>> RunWithControlledConcurrencyWorkflow(
            List<Func<Task<object?>>> asyncFunctions,
            int maxConcurrency)
        {
            if (asyncFunctions == null || asyncFunctions.Count == 0)
            {
                return new List<object?>();
            }

            // Limit concurrency to the number of available tasks
            var actualConcurrency = Math.Min(maxConcurrency, asyncFunctions.Count);

            // Create a semaphore to limit concurrency
            using var semaphore = new SemaphoreSlim(actualConcurrency, actualConcurrency);

            async Task<(int Index, object? Result)> RunWithSemaphore(int index, Func<Task<object?>> asyncFunc)
            {
                await semaphore.WaitAsync();
                try
                {
                    var result = await asyncFunc();
                    return (index, result);
                }
                finally
                {
                    semaphore.Release();
                }
            }

            // Create all tasks
            var tasks = asyncFunctions
                .Select((asyncFunc, index) => RunWithSemaphore(index, asyncFunc))
                .ToArray();

            // Wait for all tasks to complete and collect results
            var completedTasks = await Task.WhenAll(tasks);

            // Initialize results array with correct size
            var results = new List<object?>(new object?[asyncFunctions.Count]);

            // Populate results in original order
            foreach (var (index, result) in completedTasks)
            {
                results[index] = result;
            }

            return results;
        }
    }
}
