using Microsoft.Extensions.Logging;
using Temporalio.Activities;

namespace AgenticWorkflowApp.Console.Workflows.HelloWorld.Activities;

public class GetHeaderActivity
{
    [Activity("get-header-activity")]
    public Task<string> Run()
    {
        ActivityExecutionContext.Current.Logger.LogInformation("Hello from a dotnet activity!");
        return Task.FromResult("\n----- Howdy from DotNet -----\n");
    }
}
