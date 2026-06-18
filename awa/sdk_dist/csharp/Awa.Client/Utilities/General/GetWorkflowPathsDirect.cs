using System;
using System.IO;
using Awa.Client.Models;

namespace Awa.Client.Utilities.General
{
    public static partial class GeneralUtilities
    {
        /// <summary>
        /// Find the closest parent directory that contains the makefile.
        /// </summary>
        /// <param name="workflowDir">The workflow directory to start searching from</param>
        /// <returns>The path to the project root directory, or empty string if not found</returns>
        private static string FindProjectRoot(string workflowDir)
        {
            var currentDir = new DirectoryInfo(workflowDir);

            while (currentDir != null && currentDir.Parent != null)
            {
                var makefilePath = Path.Combine(currentDir.FullName, "makefile");
                if (File.Exists(makefilePath))
                {
                    return currentDir.FullName;
                }
                currentDir = currentDir.Parent;
            }

            return string.Empty; // Return empty string if no project root found
        }

        /// <summary>
        /// Get workflow paths using direct workflow type and ID parameters.
        /// </summary>
        /// <param name="workflowDir">The base workflow directory</param>
        /// <param name="workflowType">The type/name of the workflow</param>
        /// <param name="workflowId">The unique identifier of the workflow instance</param>
        /// <returns>Object containing all relevant workflow paths including project root, workflow root, input, output, BAML source, and agent prompts</returns>
        public static WorkflowPaths GetWorkflowPathsDirect(string workflowDir, string workflowType, string workflowId)
        {
            return new WorkflowPaths
            {
                ProjectRoot = FindProjectRoot(workflowDir),
                WorkflowRoot = workflowDir,
                Input = Path.Combine(workflowDir, "input"),
                Output = Path.Combine(workflowDir, "output", workflowType, workflowId),
                BamlSrc = Path.Combine(workflowDir, "baml_src"),
                AgentPrompts = Path.Combine(workflowDir, "agent_prompts")
            };
        }
    }
}
