using AgenticWorkflowApp.Console.Workflows.HelloWorld.Activities;
using AgenticWorkflowApp.Console.Workflows.HelloWorld.Models;
using Microsoft.Extensions.Logging;
using Temporalio.Workflows;
using Awa.Client.Utilities.Activity;
using Awa.Client.Utilities.General;
using System.Reflection;

namespace AgenticWorkflowApp.Console.Workflows.HelloWorld;

[Workflow("hello-world-dotnet")]
public class HelloWorldWorkflow
{
    [WorkflowRun]
    public async Task<string> RunAsync(HelloWorldWorkflowInput input)
    {
        Workflow.Logger.LogInformation("Hello from a dotnet workflow!");

        var assemblyLocation = Assembly.GetExecutingAssembly().Location;
        var binDirectory = Path.GetDirectoryName(assemblyLocation)!;
        var projectRoot = Directory.GetParent(binDirectory)?.Parent?.Parent?.FullName
            ?? throw new InvalidOperationException("Could not determine project root directory");
        var workflowDir = Path.Combine(projectRoot, "Workflows", "HelloWorld");
        var workflowPaths = GeneralUtilities.GetWorkflowPaths(
            workflowDir,
            Workflow.Info.WorkflowType,
            Workflow.Info.WorkflowId);

        var headerResult = await Workflow.ExecuteActivityAsync(
            (GetHeaderActivity a) => a.Run(),
            new ActivityOptions { StartToCloseTimeout = TimeSpan.FromMinutes(1) });

        var helloResult = await Workflow.ExecuteActivityAsync<string>(
            "awa-say-hello", // Using an AWA Python-based activity
            [input.Name],
            new ActivityOptions
            {
                StartToCloseTimeout = TimeSpan.FromMinutes(1),
                TaskQueue = "awa_default"
            });

        var addTimestampActivityInput = new AddTimestampActivityInput(
            helloResult,
            $"{headerResult}{{0}}\nat {{1}}");

        var response = await Workflow.ExecuteActivityAsync(
            (AddTimestampActivity a) => a.Run(addTimestampActivityInput),
            new ActivityOptions { StartToCloseTimeout = TimeSpan.FromMinutes(1) });

        await ActivityUtilities.WriteFileActivity(Path.Combine(workflowPaths.Output, "output.txt"), response);

        return response;
    }
}
