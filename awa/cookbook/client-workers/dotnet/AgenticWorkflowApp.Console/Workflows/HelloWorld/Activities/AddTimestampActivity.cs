using AgenticWorkflowApp.Console.Workflows.HelloWorld.Models;
using Temporalio.Activities;

namespace AgenticWorkflowApp.Console.Workflows.HelloWorld.Activities;

public class AddTimestampActivity
{
    [Activity("add-timestamp-activity")]
    public Task<string> Run(AddTimestampActivityInput input) => Task.FromResult(string.Format(
            input.Format,
            input.Input,
            DateTime.Now));
}
